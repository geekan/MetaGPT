#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/05/13
@Author  : mannaandpoem
@File    : swe_agent.py
"""
import json
import os
import re
from pathlib import Path
from typing import Literal, Optional

from datasets import load_dataset
from github.PullRequest import PullRequest
from pandas import DataFrame

from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.roles.env_manager import EnvManager
from metagpt.schema import AIMessage, Message
from metagpt.tools.libs.git import git_create_pull, git_push
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.swe_agent_commands.prompt import (
    EXAMPLE,
    INSTANCE_TEMPLATE,
    INVALID_INPUT_MESSAGE,
    NEXT_STEP_NO_OUTPUT_TEMPLATE,
    NEXT_STEP_TEMPLATE,
    ONLY_LOCATE_ISSUE_THINK_PROMPT,
    OUTPUT_FORMAT,
    SWE_AGENT_SYSTEM_TEMPLATE,
)
from metagpt.tools.swe_agent_commands.swe_agent_utils import (
    extract_repo_identifier,
    filter_and_get_repo_info,
    get_github_issue_description,
)
from metagpt.utils.common import CodeParser, find_exist_repo_path_and_cp

# Path to the bash script that sets up the default environment for the SWEAgent
SWE_SETUP_PATH = METAGPT_ROOT / "metagpt" / "tools" / "swe_agent_commands" / "setup_default.sh"
TEST_REPO_DIR = METAGPT_ROOT / "benchmark" / "swe_bench" / "data" / "test_repo"
SWE_CMD_WORK_DIR = DEFAULT_WORKSPACE_ROOT / "swe_agent_workdir"

TEST_REPO_DIR.mkdir(parents=True, exist_ok=True)
SWE_CMD_WORK_DIR.mkdir(parents=True, exist_ok=True)


class TrajectoryNode:
    def __init__(self, observation, action, thought):
        self.thought = thought
        self.action = action
        self.observation = observation

    def to_json(self):
        return {"thought": self.thought, "action": self.action, "observation": self.observation}


class SWEAgent(DataInterpreter):
    name: str = "Swen"
    profile: str = "Maintenance Engineer"
    goal: str = "Fix the bug in the code of the given repo or file."
    constraints: str = (
        "You can only enter one command at a time. You should always wait for feedback after every command."
    )

    max_react_loop: int = 20  # used for react mode
    react_mode: Literal["plan_and_act", "react"] = "react"
    user_requirement: str = ""

    # The terminal to run the bash commands
    terminal: Terminal = None
    # Bash window is the number of lines that the bash command prompt can display
    bash_window_size: int = 100
    # The memory window to restrict the number of messages in the working memory
    use_memory_window: bool = False
    memory_window: int = 4
    cur_file: str = ""
    # Fetch the base commit and issue description from the dataset
    fetch_from_dataset: Optional[bool] = False
    # git_push_and_create_pr_tag are used to determine if to push the changes to the repo and create a pull request
    git_push_and_create_pr_tag: Optional[bool] = False
    # The issue description
    issue: str = ""
    # Whether to only locate the issue without fixing it in the repo
    only_locate_issue: Optional[bool] = False
    # Path to the repository where the code is located
    repo_path: Path = SWE_CMD_WORK_DIR / "temp"
    # repo_info includes the base commit, issue description, repo identifier and hints text
    repo_info: dict = {}
    # The instance_id of the SWE-bench dataset
    instance_ids: list[str] = []
    cur_instance_id: str = ""
    # Trajectory of the agent
    trajectory: list[TrajectoryNode] = []
    dataset_path: str = ""
    dataset: DataFrame = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.terminal = Terminal()
        # Source the setup script to set up the default environment
        self.terminal.run_command(f'source {SWE_SETUP_PATH.as_posix()}')
        # Test swe_agent_commands
        # logger.info(self.terminal.run_command("open role.py"))
        self.llm.system_prompt = SWE_AGENT_SYSTEM_TEMPLATE.format(WINDOW=self.bash_window_size)
        self.trajectory.append(TrajectoryNode(thought="", action="", observation=f"SYSTEM:\n{self.llm.system_prompt}"))

        self.swe_result_dir = SWE_CMD_WORK_DIR / f"result_{self.config.llm.model}"
        if self.fetch_from_dataset:
            logger.info(f"loading {self.dataset_path} dataset")
            dataset = load_dataset(self.dataset_path)

            # Filter the dataset based on the instance_ids
            self.dataset, self.repo_info = filter_and_get_repo_info(
                dataset["test"].to_pandas(), "instance_id", self.swe_result_dir, self.instance_ids
            )
            # Update the instance_ids with the filtered dataset
            self.instance_ids = self.dataset["instance_id"].tolist()
            logger.info(f"Instance IDs: {self.instance_ids}")
            assert self.instance_ids

    async def _react(self) -> Message:
        actions_taken = 0
        rsp = AIMessage(content="No actions taken yet")  # will be overwritten after Role _act
        submit_flag = True
        while actions_taken < self.rc.max_react_loop or self.instance_ids:
            # Determine if we need to reset the environment for the next instance
            if submit_flag or actions_taken >= self.rc.max_react_loop:
                if actions_taken >= self.rc.max_react_loop:
                    # Reset the actions taken and save the trajectory and predictions if the max_react_loop is reached
                    actions_taken = await self._reset_taken_after_max_actions()

                # Check if there are any instances left to process
                if not self.instance_ids:
                    logger.error("All instances have been processed.")
                    break

                # if there are any, reset the environment for the next instance
                self._initialize_next_instance()

                submit_flag = False

            # think
            has_todo = await self._think()
            if not has_todo:
                break

            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()

            # Check if the user has submitted the changes to the repository
            if rsp.content == "submit":
                submit_flag = True

            actions_taken += 1

        # Ensure final save operations if loop ends
        await self.save_traj_and_preds()

        return rsp

    async def _reset_taken_after_max_actions(self):
        await self.save_traj_and_preds()
        self.cur_instance_id = ""
        self.working_memory.clear()
        self.trajectory.clear()
        actions_taken = 0
        return actions_taken

    def _initialize_next_instance(self):
        # Initialize the next instance from the dataset
        self.cur_instance_id = self.instance_ids.pop(0)
        instance = self.dataset.set_index("instance_id").loc[self.cur_instance_id].to_dict()
        logger.info(f"Resetting the virtual environment for the current instance: {self.cur_instance_id}")
        self._reset_env(instance)

        self.terminal.run_command(f"cd {self.repo_path}")
        self.working_memory.add(Message(content=f"cd {self.repo_path}", role="user"))
        self.trajectory.append(TrajectoryNode(thought="", action="", observation=self.user_requirement))

    async def save_traj_and_preds(self):
        if self.repo_info[self.cur_instance_id]["exit_status"] != "submitted":
            logger.info("Submitting the changes to the repository.")
            await self.submit()
        self.save_trajectory()
        self.save_predictions()

    async def _think(self) -> bool:
        """Useful in 'react' mode."""
        context = self.working_memory.get()
        if not context:
            self._set_state(0)
            return True

        if not self.rc.todo or not self.cur_instance_id:
            self._set_state(-1)
            return False

        need_action = True

        # If only_locate_issue is True, think about whether to complete the task of locating the issue
        if self.only_locate_issue:
            need_action = await self._handle_only_locate_issue(context)
        else:
            self._set_state(0)

        return need_action

    async def _handle_only_locate_issue(self, context):
        # Handle the logic for only locating the issue
        prompt = ONLY_LOCATE_ISSUE_THINK_PROMPT.format(user_requirement=self.user_requirement, context=context)
        rsp = await self.llm.aask(prompt)
        rsp_dict = json.loads(CodeParser.parse_code(block=None, text=rsp))
        need_action = rsp_dict["state"]
        self._set_state(0) if need_action else self._set_state(-1)
        self.rc.memory.add(Message(content=str(rsp_dict["location"]), role="assistant"))
        return need_action

    async def _act(self):
        """Perform an action in the environment"""
        context = "\n\n".join([str(msg) for msg in self.working_memory.get()])
        logger.info(f"Current terminal directory: {self.terminal.run_command('pwd')}")

        prompt = NEXT_STEP_TEMPLATE.format(
            user_requirement=self.user_requirement,
            observation=context,
            open_file=self.cur_file,
            working_dir=self.terminal.run_command("pwd"),
            output_format=OUTPUT_FORMAT,
            example=EXAMPLE,
        )
        response = await self.llm.aask(prompt)

        self.add_to_working_memory(response, "assistant")

        # Parse response
        thought, action = self.parse_response(response)

        # If submit is in the output, finish the task
        if "submit" in action:
            return await self._handle_submit_action(thought, action)

        logger.info(f"Action: {action}")
        # Execute the action
        observation = self._execute_action(action)
        logger.info(f"Observation: {observation}")

        self.add_to_working_memory(observation, "user")
        self.trajectory.append(TrajectoryNode(thought=thought, action=action, observation=observation))

        return Message(content=observation, role="user")

    async def _handle_submit_action(self, thought, action):
        """Handle the submit action"""
        self.add_to_working_memory(action, "user")
        self.trajectory.append(TrajectoryNode(thought=thought, action=action, observation="Submit successful."))
        self.rc.todo = None

        logger.info("Submitting the changes to the repository.")
        await self.submit()
        self.repo_info[self.cur_instance_id]["exit_status"] = "submitted"

        return Message(content="submit", role="user")

    def _execute_action(self, action):
        """Execute the given action and return the observation"""
        if action:
            observation = self.terminal.run_command(action)
            if not observation:
                observation = NEXT_STEP_NO_OUTPUT_TEMPLATE.format(
                    open_file=self.cur_file, working_dir=self.terminal.run_command("pwd")
                )
        else:
            observation = INVALID_INPUT_MESSAGE

        # Truncate the observation to 6000 characters
        observation = observation[:6000]

        return observation

    def save_trajectory(self):
        traj_path = self.swe_result_dir / f"{self.cur_instance_id}.traj"
        trajectory_actions = "\n->\n".join([node.action for node in self.trajectory])
        logger.info(f"Actions of trajectory:\n{trajectory_actions}")

        # Converts the entire trajectory list to JSON.
        trajectory_list = [node.to_json() for node in self.trajectory]

        # Save the trajectory to a JSON file
        log_dict = {
            "trajectory": trajectory_list,
            "info": self.repo_info[self.cur_instance_id],
        }
        with open(traj_path, "w") as f:
            json.dump(log_dict, f, indent=2)

        logger.info(f"Saved trajectory of {self.cur_instance_id} to {str(traj_path)}")

    def save_predictions(self):
        output_file = self.swe_result_dir / "all_preds.jsonl"
        datum = {
            "model_name_or_path": self.config.llm.model,
            "instance_id": self.cur_instance_id,
            "model_patch": self.repo_info[self.cur_instance_id]["submission"],
        }

        logger.info(f"Preparing to save predictions to {output_file}")

        # Save the predictions to a JSONL file
        with open(output_file, "a+") as fp:
            print(json.dumps(datum), file=fp, flush=True)

        logger.info(f"Saved prediction of {self.cur_instance_id} to {output_file}")

    @staticmethod
    def parse_response(response: str) -> tuple[str, str]:
        """Parsing LLM responses to extract ideas, actions and outputs from them"""
        try:
            response = json.loads(CodeParser.parse_code(text=response, block=None))

            thought, action = response.get("thought", ""), response.get("bash_command", "")

            if not action:
                raise ValueError("Invalid thought or action in response.")
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            thought, action = "", ""

        return thought, action

    def add_to_working_memory(self, content, role, use_memory_window=False) -> None:
        """Add the message to the working memory。"""
        self.working_memory.add(Message(content=content, role=role))
        if self.working_memory.count() > self.memory_window and use_memory_window:
            self.working_memory.pop(0)

    async def submit(self):
        """Submit the modified file by git in the terminal."""
        try:
            self.terminal.run_command(f"cd {self.repo_path}")
            # Generate patch by git diff
            diff_output = self.terminal.run_command("git diff")
            logger.info(f"Diff output: {diff_output}")

            # Add the patch and exit status to the repo_info
            self.repo_info[self.cur_instance_id]["submission"] = diff_output

            if self.git_push_and_create_pr_tag:
                commit_message = "Fix the bug in the code"
                # Handle the commit and push changes to the repository
                self._handle_commit(commit_message)
                # Create and switch to a new branch
                await self._handle_push_and_create_pr(commit_message)
        except Exception as e:
            logger.error(f"Error during submission: {e}")

    def _handle_commit(self, commit_message):
        # Change to the repository path and add all files to staging
        add_output = self.terminal.run_command("git add .")
        logger.info(f"Add output: {add_output}")

        # Commit the changes with a specific message
        commit_command = f'git commit -m "{commit_message}"'
        commit_output = self.terminal.run_command(commit_command)
        logger.info(f"Commit output: {commit_output}")

    async def _handle_push_and_create_pr(self, commit_message):
        """Handle pushing changes and creating a pull request."""
        new_branch = "bugfix-branch"
        checkout_command = f"cd {self.repo_path} && git checkout -b {new_branch}"
        checkout_output = self.terminal.run_command(checkout_command)
        logger.info(f"Checkout output: {checkout_output}")

        # Push the changes to the new branch using git_push
        access_token = os.getenv("GITHUB_TOKEN")
        branch = await git_push(
            local_path=self.repo_path, access_token=access_token, comments=commit_message, new_branch=new_branch
        )
        logger.info(f"Pushed to branch: {branch.head}")

        # Create a pull request using git_create_pull
        pull_request = await git_create_pull(
            base=branch.base,
            head=branch.head,
            base_repo_name=branch.repo_name,
            access_token=access_token,
            title="Fix the bug in the code",
            body="This pull request fixes the bug in the code.",
        )
        if isinstance(pull_request, PullRequest):
            logger.info(f"Created pull request: {pull_request}")
        if isinstance(pull_request, str):
            logger.info(f"Visit this url to create a new pull request: '{pull_request}'")

    def preprocess_repo(self):
        """Preprocess the repo information."""
        # If the repo information is provided, preprocess the repo information
        logger.info("Starting to preprocess the repo information.")
        if self.repo_info:
            self.clone_and_checkout_repo(
                repo_identifier=self.repo_info[self.cur_instance_id]["repo"],
                base_commit=self.repo_info[self.cur_instance_id]["base_commit"],
            )
            self.issue = self.repo_info[self.cur_instance_id]["issue_description"]

            self.user_requirement = INSTANCE_TEMPLATE.format(
                user_requirement=self.user_requirement,
                issue=self.issue,
                hints_text=self.repo_info[self.cur_instance_id]["hints_text"],
            )
        # Only locate the issue without fixing it
        elif self.only_locate_issue:
            self.user_requirement = (
                f"## User Requirement\n{self.user_requirement}\n\n## Issue Description\n{self.issue}"
            )
        # If the issue description is not provided, preprocess the repo information from the issue link of content
        elif not self.issue:
            self._preprocess_repo_with_link(self.user_requirement)
            self.user_requirement = INSTANCE_TEMPLATE.format(
                user_requirement=self.user_requirement,
                issue=self.issue,
                hints_text=self.repo_info[self.cur_instance_id]["hints_text"],
            )
        logger.info(f"User Requirement:\n{self.user_requirement}")

    def _preprocess_repo_with_link(self, content: str) -> None:
        """Preprocess the repo information from the Github issue link."""
        repo_identifier = extract_repo_identifier(content)

        if repo_identifier:
            self.clone_and_checkout_repo(repo_identifier)
            owner, repo_name = repo_identifier.split("/")

            # todo: Extract issue URL, may need to modify
            issue_url_match = re.search(r"https://github\.com/[^/]+/[^/]+/issues/\d+", content)
            if issue_url_match:
                issue_url = issue_url_match.group(0)
                issue_number = int(issue_url.split("/")[-1])
                self.issue = get_github_issue_description(owner, repo_name, issue_number)

        self.terminal.run_command(f"cd {self.repo_path}")

    def clone_and_checkout_repo(self, repo_identifier: str = "", base_commit: str = "") -> None:
        if base_commit:
            # self.repo_path = os.path.join(TEST_REPO_DIR.as_posix(), self.repo_info[self.cur_instance_id]["env_name"])
            self.repo_path = TEST_REPO_DIR / self.repo_info[self.cur_instance_id]["env_name"]
        else:
            # self.repo_path = os.path.join(TEST_REPO_DIR.as_posix(), repo_identifier.split("/")[-1])
            self.repo_path = TEST_REPO_DIR / repo_identifier.split("/")[-1]

        clone_command = f"git clone 'https://github.com/{repo_identifier}.git' {self.repo_path}"
        checkout_command = f"cd {self.repo_path} && git checkout -f {base_commit}" if base_commit else ""

        if not self.repo_path.exists() or (not any(self.repo_path.rglob("*.py"))):
            # re-use an existed same repo_name repo
            new_dest_path = find_exist_repo_path_and_cp(self.repo_path)
            if not new_dest_path:
                clone_result = self.terminal.run_command(clone_command)
                logger.info(clone_result)
        else:
            logger.info(f"using a existing repo path: {self.repo_path}")
        checkout_result = self.terminal.run_command(checkout_command)
        logger.info(checkout_result)

    def _reset_env(self, instance: dict) -> None:
        """Reset the environment."""
        # self.env_name = ENV_INFO_DATA.get(self.cur_instance_id, "")
        env_name = self.repo_info[self.cur_instance_id]["env_name"]

        # repo_name = instance["repo"].split("/")[-1]
        repo_name = self.repo_info[self.cur_instance_id]["repo"].split("/")[-1]

        # preprocess_repo will clone the repo and checkout the base commit
        self.preprocess_repo()

        # Create the environment manager
        env_manager = EnvManager(
            env_name=env_name, repo_path=str(self.repo_path), instance=instance, repo_name=repo_name
        )
        env_manager.create_env()


if __name__ == "__main__":
    import asyncio

    dataset_path = "manna-ai/SWE-bench_Nano"
    instance_ids = ["django__django-16595", "django__django-16229"]
    # Do not perform test case to verify the fix
    requirement = "Fix the bug in the repo. Do not perform test case to verify the fix."
    swe_agent = SWEAgent(
        instance_ids=instance_ids,
        fetch_from_dataset=True,
        user_requirement=requirement,
        dataset_path=dataset_path,
    )
    asyncio.run(swe_agent.run(requirement))

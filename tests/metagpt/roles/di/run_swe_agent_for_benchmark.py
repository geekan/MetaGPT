import argparse
import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from metagpt.config2 import config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.swe_agent_commands.swe_agent_utils import load_hf_dataset

# Specify by yourself
TEST_REPO_DIR = METAGPT_ROOT / "data" / "test_repo"
DATA_DIR = METAGPT_ROOT / "data/hugging_face"

INSTANCE_TEMPLATE = """
## User Requirement
Fix the bug in the repo. Because the environment is not available, you DO NOT need to run and modify any existing test case files or add new test case files to ensure that the bug is fixed.

We're currently solving the following issue within our repository. You can use any bash commands or the special interface to help you. Here's the issue and hints text:
## ISSUE
{issue}

## HINTS
hints text is the comment under issue:
{hints_text}

The repository may already exist at the path `{repo_path}`. If it doesn't, please download the repository to this path.
Your first action must be to navigate to the repository path `{repo_path}`.
This issue occurred in version {version}, with the corresponding base commit being {base_commit}. You need to switch to the code version associated with this commit.
All subsequent actions must be performed within this repository path. Do not leave this directory to execute any actions at any time.

# INSTRUCTIONS:
Now, you're going to solve this issue on your own from the perspective of a programmer. Your terminal session has started and you're in the repository's root directory. You can use any bash commands or the special interface to help you. Edit all the files you need. 
Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. You should always wait for feedback after every command.
"""


def check_instance_status(instance, swe_result_dir):
    output_file = swe_result_dir / "all_preds.jsonl"
    res = True
    # 先检查all_preds.jsonl文件是否存在
    if not output_file.exists():
        return res
    with open(output_file, "r") as fp:
        for line in fp:
            existing_instance = json.loads(line.strip())
            if existing_instance["instance_id"] == instance["instance_id"]:
                return False
    return True


async def terminal_run_command(cmd, terminal):
    cmd_output = await terminal.run_command(cmd)
    logger.info(f"command:{cmd} output:\n {cmd_output}")
    return cmd_output


async def refresh_repo(instance, test_repo_dir, reclone_existing_repo=False):
    terminal = Terminal()
    try:
        repo_path = Path(test_repo_dir) / (
            instance["repo"].replace("-", "_").replace("/", "__") + "_" + instance["version"]
        )
        repo_identifier = instance["repo"]
        base_commit = instance["base_commit"]
        if os.path.exists(repo_path) and reclone_existing_repo is True:
            logger.info(f"remove exist repo path:{repo_path.absolute()}")
            shutil.rmtree(repo_path)
        if os.path.exists(repo_path):
            logger.info(f"reset exist repo path:{repo_path.absolute()}")
            for cmd in [
                f"cd {repo_path.absolute()}",
                "git reset --hard && git clean -n -d && git clean -f -d",
                "BRANCH=$(git remote show origin | awk '/HEAD branch/ {print $NF}')",
                'git checkout "$BRANCH"',
                "git branch",
                "pwd",
            ]:
                await terminal_run_command(cmd, terminal)
        else:
            logger.info(f"clone repo to path:{repo_path}")
            for cmd in [
                f"git clone 'https://github.com/{repo_identifier}.git' {repo_path.absolute()}",
                f"cd {repo_path.absolute()}" + f" && git checkout -f {base_commit}" if base_commit else "",
                "git branch",
                "pwd",
            ]:
                await terminal_run_command(cmd, terminal)
    except Exception as e:
        logger.warning(e)
    finally:
        await terminal.close()
    return repo_path


async def get_git_diff(instance, test_repo_dir):
    git_diff = ""
    terminal = Terminal()
    try:
        repo_path = Path(test_repo_dir) / (
            instance["repo"].replace("-", "_").replace("/", "__") + "_" + instance["version"]
        )
        # ignore backup file and submit stage
        for cmd in [f"cd {repo_path.absolute()} ", "echo '.backup.*' >> .gitignore", "git add -A"]:
            await terminal_run_command(cmd, terminal)
        git_diff = await terminal_run_command("git diff --cached", terminal)
    except Exception as e:
        logger.error(f"Error during submission: {e}")
    finally:
        await terminal.close()
    return git_diff


async def run(instance, swe_result_dir, args):
    if not check_instance_status(instance, swe_result_dir):
        logger.info(f"Instance {instance['instance_id']} already exists, skipping execution.")
        return

    # preparation for the repo
    logger.info(f"**** Preparing to run {instance['instance_id']}****")
    test_repo_dir = args.test_repo_dir
    repo_path = await refresh_repo(instance, test_repo_dir, args.reclone_existing_repo)

    user_requirement_and_issue = INSTANCE_TEMPLATE.format(
        issue=instance["problem_statement"],
        hints_text=instance["hints_text"],
        repo_path=repo_path.absolute(),
        version=instance["version"],
        base_commit=instance["base_commit"],
    )

    logger.info(f"**** Starting to run {instance['instance_id']}****")
    logger.info("User Requirement:\n" + user_requirement_and_issue)
    try:
        editor = Editor(enable_auto_lint=True, working_dir=Path(repo_path))
        engineer = Engineer2(run_eval=True, editor=editor)
        await asyncio.wait_for(engineer.run(user_requirement_and_issue), timeout=args.max_wait_time_per_case * 60)
    except Exception as e:
        logger.warning(f"**** exception lead to end: {instance['instance_id']}****\n\nerror:{e}")
    # save the difference of repo
    await save_predictions(engineer, instance, test_repo_dir, swe_result_dir)
    logger.info(f"**** Finished running {instance['instance_id']}****")


async def save_predictions(engineer, instance, test_repo_dir, swe_result_dir):
    output_file = swe_result_dir / "all_preds.jsonl"
    instance["model_name_or_path"] = engineer.config.llm.model
    instance["model_patch"] = await get_git_diff(instance, test_repo_dir)
    logger.info(f"'model_patch':\n{instance['model_patch']}")
    logger.info(f"Preparing to save predictions to {output_file}")

    # Save the predictions to a JSONL file
    with open(output_file, "a+") as fp:
        print(json.dumps(instance), file=fp, flush=True)

    logger.info(f"Saved prediction of {instance['instance_id']} to {output_file}")


async def async_main(args):
    dataset_path = "manna-ai/SWE-bench_Nano"  # "princeton-nlp/SWE-bench_Lite" #"manna-ai/SWE-bench_Nano"
    dataset = load_hf_dataset(dataset_name_or_path=dataset_path, cache_dir=DATA_DIR, split="test")
    swe_result_dir = Path(args.save_folder)
    if swe_result_dir.exists():
        logger.info(f"{swe_result_dir} exists; resuming test from last checkpoint.")
    swe_result_dir.mkdir(parents=True, exist_ok=True)
    for index, instance in enumerate(dataset):
        # switch to a new logger file
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        logger.add(swe_result_dir / "logs" / f"{index+1}_{instance['instance_id']}.log", level="DEBUG")
        await run(instance, swe_result_dir, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="the argument of scripts")
    # 添加参数
    swe_result_dir = (
        DEFAULT_WORKSPACE_ROOT
        / f"result_{config.llm.model.replace('/', '_')}_start_time_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S') }"
    )
    test_repo_dir = TEST_REPO_DIR.absolute()
    swe_result_dir = swe_result_dir.absolute()
    parser.add_argument(
        "-rw", "--test_repo_dir", default=test_repo_dir, help="The directory to save temporary repositories", type=str
    )
    parser.add_argument("-s", "--save_folder", default=swe_result_dir, help="Folder to save results and logs", type=str)
    parser.add_argument(
        "-mwtc",
        "--max_wait_time_per_case",
        default=10,
        help="Maximum wait time allowed per test case (in minutes)",
        type=int,
    )
    parser.add_argument(
        "-o",
        "--reclone_existing_repo",
        action="store_true",
        help="If set, the existing repository will be removed and recloned.",
    )
    # 解析命令行参数
    args = parser.parse_args()
    asyncio.run(async_main(args))


"""
#
python tests/metagpt/roles/di/run_swe_agent_for_benchmark.py \
--test_repo_dir "./data/test_repo" \
--save_folder "./workspace/deepseek_coder_0907" \
--max_wait_time_per_case 10 
"""

"""
# 重新克隆仓库
python tests/metagpt/roles/di/run_swe_agent_for_benchmark.py \
--test_repo_dir "./data/test_repo" \
--save_folder "./workspace/deepseek_coder_0907" \
--max_wait_time_per_case 10 \
--reclone_existing_repo
"""

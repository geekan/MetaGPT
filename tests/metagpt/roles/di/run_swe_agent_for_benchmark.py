import asyncio
import json
import os
import shutil
import sys
from datetime import datetime

from metagpt.config2 import Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.swe_agent_commands.swe_agent_utils import load_hf_dataset

config = Config.default()
# Specify by yourself
Role = Engineer2
# 调整每个样例的执行时间，太低容易出现提交u数量少的情况
MAX_MINUTES_PRE_INSTANCE = 20
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


async def run(instance, swe_result_dir):
    if not check_instance_status(instance, swe_result_dir):
        logger.info(f"Instance {instance['instance_id']} already exists, skipping execution.")
        return

    repo_path = TEST_REPO_DIR / (instance["repo"].replace("-", "_").replace("/", "__") + "_" + instance["version"])
    # 下载仓库
    logger.info(f"repo_path:{repo_path}")
    if os.path.exists(repo_path):
        # 删除已有的仓库
        logger.info(f"remove exist repo path:{repo_path}")
        shutil.rmtree(repo_path)
    # 下载仓库 并切换分支
    terminal = Terminal()
    repo_identifier = instance["repo"]
    base_commit = instance["base_commit"]
    clone_command = f"git clone 'https://github.com/{repo_identifier}.git' {repo_path}"
    checkout_command = f"cd {repo_path} && git checkout -f {base_commit}" if base_commit else ""
    await terminal.run_command(clone_command)
    ignore_temp_file_cmd = "echo '.backup.*' >> .gitignore"
    logger.info(await terminal.run_command(checkout_command))
    logger.info(await terminal.run_command("git branch"))
    await terminal.run_command(ignore_temp_file_cmd)

    user_requirement_and_issue = INSTANCE_TEMPLATE.format(
        issue=instance["problem_statement"],
        hints_text=instance["hints_text"],
        repo_path=repo_path,
        version=instance["version"],
        base_commit=instance["base_commit"],
    )

    logger.info(f"**** Starting to run {instance['instance_id']}****")
    logger.info("User Requirement", user_requirement_and_issue)
    try:
        role = Role(run_eval=True, editor=Editor(enable_auto_lint=True))
        await asyncio.wait_for(role.run(user_requirement_and_issue), timeout=MAX_MINUTES_PRE_INSTANCE * 60)
    except Exception as e:
        print(e)
        logger.info(f"**** exception lead to end: {instance['instance_id']}****")
        pass

    save_predictions(role, instance, swe_result_dir)
    logger.info(f"**** Finished running {instance['instance_id']}****")


def save_predictions(role, instance, swe_result_dir):
    output_file = swe_result_dir / "all_preds.jsonl"
    instance["model_name_or_path"] = role.config.llm.model
    instance["model_patch"] = role.output_diff
    logger.info("model_patch:" + role.output_diff)
    logger.info(f"Preparing to save predictions to {output_file}")

    # Save the predictions to a JSONL file
    with open(output_file, "a+") as fp:
        print(json.dumps(instance), file=fp, flush=True)

    logger.info(f"Saved prediction of {instance['instance_id']} to {output_file}")


async def async_main():
    dataset_path = "manna-ai/SWE-bench_Nano"  # "princeton-nlp/SWE-bench_Lite" #"manna-ai/SWE-bench_Nano"

    dataset = load_hf_dataset(dataset_name_or_path=dataset_path, cache_dir=DATA_DIR, split="test")
    date_time = datetime.now().strftime("%m%d")
    _round = "first"

    exp_name = f"nano_mgx_{date_time}_{_round}"

    now = datetime.now()
    formatted_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    swe_result_dir = (
        DEFAULT_WORKSPACE_ROOT / f"result_{config.llm.model.replace('/', '_')}_start_time_{formatted_time}" / exp_name
    )
    # swe_result_dir = (
    #     DEFAULT_WORKSPACE_ROOT / f"result_{config.llm.model.replace('/', '_')}" / exp_name
    # )
    swe_result_dir.mkdir(parents=True, exist_ok=True)
    for index, instance in enumerate(dataset):
        # switch to a new logger file
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        logger.add(swe_result_dir / f"{index+1}_{instance['instance_id']}.log", level="DEBUG")
        await run(instance, swe_result_dir)


if __name__ == "__main__":
    asyncio.run(async_main())

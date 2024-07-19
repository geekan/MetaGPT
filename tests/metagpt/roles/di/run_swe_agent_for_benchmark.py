import asyncio
import json
from datetime import datetime

from metagpt.config2 import config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.roles.di.swe_agent import SWEAgent
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


async def run(instance, swe_result_dir):
    if not check_instance_status(instance, swe_result_dir):
        logger.info(f"Instance {instance['instance_id']} already exists, skipping execution.")
        return

    repo_path = TEST_REPO_DIR / (instance["repo"].replace("-", "_").replace("/", "__") + "_" + instance["version"])

    # 前处理
    terminal = Terminal()
    await terminal.run_command(f"cd {repo_path} && git reset --hard && git clean -n -d && git clean -f -d")
    await terminal.run_command("BRANCH=$(git remote show origin | awk '/HEAD branch/ {print $NF}')")
    logger.info(await terminal.run_command("echo $BRANCH"))
    logger.info(await terminal.run_command('git checkout "$BRANCH"'))
    logger.info(await terminal.run_command("git branch"))

    user_requirement_and_issue = INSTANCE_TEMPLATE.format(
        issue=instance["problem_statement"],
        hints_text=instance["hints_text"],
        repo_path=repo_path,
        version=instance["version"],
        base_commit=instance["base_commit"],
    )

    logger.info(f"**** Starting to run {instance['instance_id']}****")
    swe_agent = SWEAgent()
    swe_agent.run_eval = True
    await swe_agent.run(user_requirement_and_issue)
    save_predictions(swe_agent, instance, swe_result_dir)
    logger.info(f"**** Finished running {instance['instance_id']}****")


def save_predictions(swe_agent: SWEAgent, instance, swe_result_dir):
    output_file = swe_result_dir / "all_preds.jsonl"
    instance["model_name_or_path"] = swe_agent.config.llm.model
    instance["model_patch"] = swe_agent.output_diff

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
    # _round = "second"
    exp_name = f"nano_mgx_{date_time}_{_round}"
    swe_result_dir = DEFAULT_WORKSPACE_ROOT / f"result_{config.llm.model.replace('/', '_')}" / exp_name
    swe_result_dir.mkdir(parents=True, exist_ok=True)
    for instance in dataset:
        await run(instance, swe_result_dir)


if __name__ == "__main__":
    asyncio.run(async_main())

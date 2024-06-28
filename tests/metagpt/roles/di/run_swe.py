import asyncio
import json
from datetime import datetime
from pathlib import Path

from metagpt.config2 import config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.roles.di.swe import SWE
from metagpt.tools.swe_agent_commands.swe_agent_utils import load_hf_dataset

# Specify by yourself
TEST_REPO_DIR = Path("/Users/seeker/Projects/sdfz/mg/mg-swe-agent") / "benchmark" / "swe_bench" / "data" / "test_repo"
DATA_DIR = METAGPT_ROOT / "benchmark" / "swe_bench" / "data"

INSTANCE_TEMPLATE = """
## User Requirement
Fix the bug in the repo. Because the environment is not available, you DO NOT need to run and modify any existing test case files or add new test case files to ensure that the bug is fixed.

We're currently solving the following issue within our repository. You can use any bash commands or the special interface to help you. Here's the issue and hints text:
## ISSUE
{issue}

## HINTS
hints text is the comment under issue:
{hints_text}

The repo may already exist at the path `{repo_path}` (if not, please download the repo to this path). 
This issue occurred in version {version}, with the corresponding base commit being {base_commit}, you need to switch to the code version corresponding to this commit.

# INSTRUCTIONS:
Now, you're going to solve this issue on your own from the perspective of a programmer. Your terminal session has started and you're in the repository's root directory. You can use any bash commands or the special interface to help you. Edit all the files you need. 
Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. You should always wait for feedback after every command.
"""


def split_dataset_equally(dataset):
    # 计算索引
    # fixme: 设置django

    part1 = dataset.filter(
        lambda x: x["repo"]
        not in [
            "django/django",
            "sympy/sympy",
            "pytest-dev/pytest",
        ],
        desc="Filtering out existing ids",
        load_from_cache_file=True,
    )

    part2 = dataset.filter(
        lambda x: x["repo"] in ["sympy/sympy", "pytest-dev/pytest"],
        desc="Filtering out existing ids",
        load_from_cache_file=True,
    )

    part3 = dataset.filter(
        lambda x: x["repo"] in ["django/django"],
        desc="Filtering out existing ids",
        load_from_cache_file=False,
    )

    print(len(part1), len(part2), len(part3))

    return [part1, part2, part3]


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

    user_requirement_and_issue = INSTANCE_TEMPLATE.format(
        issue=instance["problem_statement"],
        hints_text=instance["hints_text"],
        repo_path=repo_path,
        version=instance["version"],
        base_commit=instance["base_commit"],
    )

    logger.info(f"**** Starting to run {instance['instance_id']}****")
    swe_agent = SWE()
    await swe_agent.run(user_requirement_and_issue)
    save_predictions(swe_agent, instance, swe_result_dir)
    logger.info(f"**** Finished running {instance['instance_id']}****")


def save_predictions(swe_agent: SWE, instance, swe_result_dir):
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
    sample_datasets = split_dataset_equally(dataset)
    date_time = datetime.now().strftime("%m-%d")
    round_ = "first"

    for idx, sub_dataset in enumerate(sample_datasets):
        exp_name = f"Nano-test-{date_time}-{round_}-part-{idx}"
        swe_result_dir = DEFAULT_WORKSPACE_ROOT / "swe_agent_workdir" / f"result_{config.llm.model}" / exp_name
        swe_result_dir.mkdir(parents=True, exist_ok=True)
        for instance in sub_dataset:
            await run(instance, swe_result_dir)


if __name__ == "__main__":
    asyncio.run(async_main())

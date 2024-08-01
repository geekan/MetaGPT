# -*- coding: utf-8 -*-
# @Date    : 7/7/2024 17:07 PM
# @Author  : didi
# @Desc    : test on human eval graph

import asyncio
import json
import os
import subprocess
import sys
from typing import Literal, Optional

import aiofiles
from evalplus.data import get_human_eval_plus

from examples.ags.w_action_node.graph import HumanEvalGraph
from examples.ags.w_action_node.operator import GenerateCode, GenerateCodeBlock
from examples.ags.w_action_node.utils import sort_json_by_key
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.common import add_jsonl_file, read_json_file
from metagpt.utils.exceptions import handle_exception

generate_code = GenerateCode(llm=LLM())
generate_code_block = GenerateCodeBlock(llm=LLM())
solver = HumanEvalGraph(name="solver", llm=LLM(), criteria="correctness, efficiency, readability", vote_count=5)

ModeType = Literal["ags", "alpha_codium", "llm"]


async def llm_generate(id):
    case = get_human_eval_plus()[f"{id}"]
    solution_result = await generate_code_block(case["prompt"], case["entry_point"])
    sample_dict = dict(task_id=case["task_id"], solution=solution_result["code_solution"])
    return sample_dict


async def ags_generate(id, ensemble_count: int = 5):
    case = get_human_eval_plus()[f"{id}"]
    solution_result = await solver(case["prompt"], ensemble_count=ensemble_count)
    sample_dict = dict(task_id=case["task_id"], solution=solution_result["final_solution"])
    return sample_dict


async def alpha_codium_generate(id):
    case = get_human_eval_plus()[f"{id}"]
    solution_result = await solver.alpha_codium(case["task_id"], case["prompt"], ensemble_count=5)
    sample_dict = dict(task_id=case["task_id"], solution=solution_result["final_solution"])
    return sample_dict


async def route_generate(mode: ModeType, id: str):
    if mode == "ags":
        sample_dict = await ags_generate(id)
    elif mode == "alpha_codium":
        sample_dict = await alpha_codium_generate(id)
    elif mode == "llm":
        sample_dict = await llm_generate(id)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    return sample_dict


async def sample_generate(id, result_path: str = "samples.jsonl", mode: ModeType = "ags"):
    sample_dict = await route_generate(mode, id)
    add_jsonl_file(result_path, [sample_dict])
    sort_json_by_key(result_path, result_path)


async def samples_generate(mode: ModeType, result_path: str = "samples.jsonl"):
    ids = list(get_human_eval_plus().keys())
    file_lock = asyncio.Lock()

    @handle_exception(
        exception_type=Exception,
        exception_msg="Error in solve_and_write function",
        default_return=lambda id, *args, **kwargs: id,
    )
    async def solve_and_write(id: str, mode: ModeType) -> Optional[str]:
        sample_dict = await route_generate(mode, id)
        async with file_lock:
            async with aiofiles.open(result_path, mode="a") as f:
                await f.write(json.dumps(sample_dict) + "\n")
        return None

    tasks = [solve_and_write(id, mode) for id in ids]
    results = await asyncio.gather(*tasks)
    failed_tasks = [task_id for task_id in results if task_id is not None]

    if failed_tasks:
        logger.info(failed_tasks)
        for task_id in failed_tasks:
            try:
                await sample_generate(task_id, result_path, mode)
                failed_tasks.remove(task_id)
            except Exception:
                logger.error(f"{task_id} fail")

    sort_json_by_key(result_path, result_path)

    if not failed_tasks:
        if automatic_evalplus(result_path):
            eval_path = result_path[:-6] + "_eval_results.json"
            unpassed_exapmle = extract_failure_tests(eval_path)
            logger.info(unpassed_exapmle)
    else:
        logger.info(failed_tasks)


@handle_exception(exception_type=subprocess.CalledProcessError, exception_msg="sanitize error", default_return=None)
def automatic_sanitize(result_path: str = "samples.jsonl") -> Optional[str]:
    """
    在命令行中自动执行 evalplus.sanitize --samples result_path
    返回result_path前缀加上"-sanitized.jsonl"
    """
    command = ["evalplus.sanitize", "--samples", result_path]

    subprocess.run(command, check=True)

    base_name = os.path.splitext(result_path)[0]
    sanitized_path = f"{base_name}-sanitized.jsonl"

    return sanitized_path


@handle_exception(
    exception_type=subprocess.CalledProcessError,
    exception_msg="Error in automatic_evalplus function",
    default_return=False,
)
def automatic_evalplus(result_path: str = "samples.jsonl") -> bool:
    """
    在命令行中自动执行 evalplus.evaluate --dataset humaneval --samples samples.jsonl --parallel 2 --base-only
    """
    command = [
        sys.executable,  # 使用当前 Python 解释器
        "-m",
        "evalplus.evaluate",
        "--dataset",
        "humaneval",
        "--samples",
        result_path,
        "--parallel",
        "2",
        "--base-only",
    ]

    result = subprocess.run(command, check=True, capture_output=True, text=True)
    logger.info(f"ouptput: \n {result.stdout}")
    return True


def extract_failure_tests(file_path: str = "samples_eval_results.json"):
    task_results = read_json_file(file_path)

    failed_tests = []
    for task in task_results["eval"].values():
        if task[0]["base_status"] == "fail":
            failed_test = {
                "task_id": task[0]["task_id"],
            }
            failed_tests.append(failed_test)
    logger.info(f"length of failed tests: {len(failed_tests)}")

    return failed_tests

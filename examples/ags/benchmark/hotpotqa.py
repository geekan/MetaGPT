import asyncio
import json
import os
import re
import string
from typing import Literal, Optional

import aiofiles

from examples.ags.w_action_node.graph import HotpotQAGraph
from examples.ags.w_action_node.operator import Format, GenerateOnContext
from examples.ags.w_action_node.utils import get_hotpotqa
from metagpt.llm import LLM
from metagpt.logs import logger

HOTPOTQA_PATH = "hotpotqa_1000.jsonl"


def sort_json_by_key(input_path, output_path):
    with open(input_path) as f:
        data = [json.loads(line) for line in f]
    data.sort(key=lambda x: x["task_id"])
    with open(output_path, "w") as f:
        for line in data:
            f.write(json.dumps(line) + "\n")


extract_supporting_sentences = GenerateOnContext(
    llm=LLM(), requirement="supporting sentences to get the final answers (split by newline)"
)
generate_on_context = GenerateOnContext(llm=LLM(), requirement="a concise answer without additional context")
format = Format(llm=LLM())
solver = HotpotQAGraph(
    name="solver",
    llm=LLM(),
    criteria="correctness, only concise answer, without additional context",
    HOTPOTQA_PATH=HOTPOTQA_PATH,
)

ModeType = Literal["ags", "alpha_codium", "llm"]


async def llm_generate(id):
    dp = get_hotpotqa(HOTPOTQA_PATH)[id]
    paragraphs = [item[1] for item in dp["context"] if isinstance(item[1], list)]
    context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)

    supporting_sentences = await extract_supporting_sentences(dp["question"], context_str)
    supporting_sentences_str = "\n".join(supporting_sentences.get("solution"))

    answer_result = await generate_on_context(dp["question"], supporting_sentences_str)
    answer_result = answer_result.get("solution")

    answer_formated = await format(dp["question"], answer_result)
    sample_dict = dict(
        task_id=id,
        answer=answer_formated.get("solution"),
        supporting_sentences=supporting_sentences.get("solution").split("\n"),
    )
    return sample_dict


async def route_generate(mode: ModeType, id):
    if mode == "ags":
        sample_dict = await solver(id)
    elif mode == "llm":
        sample_dict = await llm_generate(id)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    return sample_dict


async def sample_generate(id, result_path: str = "samples.jsonl", mode: ModeType = "llm"):
    sample_dict = await route_generate(mode, id)
    async with aiofiles.open(result_path, mode="a") as f:
        await f.write(json.dumps(sample_dict) + "\n")
    # sort_json_by_key(result_path, result_path)


async def samples_generate(
    mode: ModeType, data_path: str = HOTPOTQA_PATH, result_path: str = "samples.jsonl", max_concurrency: int = 50
):
    ids = list(get_hotpotqa(HOTPOTQA_PATH).keys())

    file_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(max_concurrency)

    async def answer_and_write(mode: ModeType, id) -> Optional[str]:
        async with semaphore:
            try:
                sample_dict = await route_generate(mode, id)
            except Exception:
                return id
            async with file_lock:
                async with aiofiles.open(result_path, mode="a") as f:
                    await f.write(json.dumps(sample_dict) + "\n")
            return None

    tasks = [answer_and_write(mode, id) for id in ids]
    results = await asyncio.gather(*tasks)
    failed_ids = [id for id in results if id is not None]

    if failed_ids:
        logger.info(failed_ids)
        for id in failed_ids:
            try:
                await sample_generate(id, result_path, mode)
                failed_ids.remove(id)
            except Exception:
                logger.error(f"Failed to generate sample for id: {id}")

    sort_json_by_key(result_path, result_path)

    if not failed_ids:
        eval_path = result_path[:-6] + "_eval.json"
        logger.info(eval(result_path, data_path, eval_path))


def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def exact_match_score(prediction, ground_truth):
    return normalize_answer(prediction) == normalize_answer(ground_truth)


def eval(prediction_file, gold_file, eval_file):
    # if existing eval file
    if os.path.exists(eval_file):
        # read the result
        with open(eval_file) as f:
            eval_results = [json.loads(line) for line in f]
            em = sum([result["em"] for result in eval_results])
            logger.info(f"EM: {em/len(eval_results)}")
        return

    sort_json_by_key(prediction_file, prediction_file)
    with open(prediction_file) as f:
        predictions = [json.loads(line) for line in f]

    with open(gold_file) as f:
        golds = [json.loads(line) for line in f]

    eval_results = []
    em = 0
    for prediction, gold in zip(predictions, golds):
        if prediction["task_id"] != gold["_id"]:
            raise ValueError(f"Task ID {gold['_id']} do not match")
        result = exact_match_score(prediction["answer"], gold["answer"])
        em += result
        eval_results.append(
            {"task_id": prediction["task_id"], "solution": prediction["answer"], "answer": gold["answer"], "em": result}
        )

    with open(eval_file, "w") as f:
        for line in eval_results:
            f.write(json.dumps(line) + "\n")

    logger.info(f"EM: {em/len(predictions)}")

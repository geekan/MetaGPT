# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets
import asyncio
import random
from typing import Any, Dict

from metagpt.ext.spo.prompts.evaluate_prompt import EVALUATE_PROMPT
from metagpt.ext.spo.utils import load
from metagpt.ext.spo.utils.llm_client import SPO_LLM, RequestType, extract_content
from metagpt.logs import logger


class QuickExecute:
    """
    Execute Prompt
    """

    def __init__(self, prompt: str):
        self.prompt = prompt
        self.llm = SPO_LLM.get_instance()

    async def prompt_execute(self) -> tuple[Any]:
        _, _, qa, _ = load.load_meta_data()
        answers = []

        async def fetch_answer(q: str) -> Dict[str, Any]:
            messages = [{"role": "user", "content": f"{self.prompt}\n\n{q}"}]
            try:
                answer = await self.llm.responser(request_type=RequestType.EXECUTE, messages=messages)
                return {"question": q, "answer": answer}
            except Exception as e:
                return {"question": q, "answer": str(e)}

        tasks = [fetch_answer(item["question"]) for item in qa]
        answers = await asyncio.gather(*tasks)

        return answers


class QuickEvaluate:
    """
    Complete the evaluation for different answers here.
    """

    def __init__(self):
        self.llm = SPO_LLM.get_instance()

    async def prompt_evaluate(self, samples: dict, new_samples: dict) -> bool:
        _, requirement, qa, _ = load.load_meta_data()

        if random.random() < 0.5:
            samples, new_samples = new_samples, samples
            is_swapped = True
        else:
            is_swapped = False

        messages = [
            {
                "role": "user",
                "content": EVALUATE_PROMPT.format(
                    requirement=requirement, sample=samples, new_sample=new_samples, answers=str(qa)
                ),
            }
        ]

        try:
            response = await self.llm.responser(request_type=RequestType.EVALUATE, messages=messages)
            choose = extract_content(response, "choose")
            return choose == "A" if is_swapped else choose == "B"

        except Exception as e:
            logger.error(e)
            return False

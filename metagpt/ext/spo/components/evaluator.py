# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets
import asyncio
from typing import Dict, Any

from metagpt.ext.spo.utils import load
from metagpt.ext.spo.prompts.evaluate_prompt import EVALUATE_PROMPT
import random
from metagpt.ext.spo.utils.llm_client import SPO_LLM, extract_content


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
                answer = await self.llm.responser(role="execute", messages=messages)
                return {'question': q, 'answer': answer}
            except Exception as e:
                return {'question': q, 'answer': str(e)}

        tasks = [fetch_answer(item['question']) for item in qa]
        answers = await asyncio.gather(*tasks)

        return answers


class QuickEvaluate:
    """
    Complete the evaluation for different answers here.
    """

    def __init__(self):
        self.llm = SPO_LLM.get_instance()

    async def prompt_evaluate(self, sample: list, new_sample: list) -> bool:
        _, requirement, qa, _ = load.load_meta_data()

        if random.random() < 0.5:
            sample, new_sample = new_sample, sample
            is_swapped = True
        else:
            is_swapped = False

        messages = [{"role": "user", "content": EVALUATE_PROMPT.format(
            requirement=requirement,
            sample=sample,
            new_sample=new_sample,
            answers=str(qa))}]

        try:
            response = await self.llm.responser(role="evaluate", messages=messages)
            choose = extract_content(response, 'choose')

            if is_swapped:
                return choose == "A"
            return choose == "B"

        except Exception as e:
            print(e)
            return False



if __name__ == "__main__":
    execute = QuickExecute(prompt="Answer the Question，{question}")

    answers = asyncio.run(execute.prompt_evaluate())
    print(answers)

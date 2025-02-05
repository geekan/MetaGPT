# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets
import asyncio
from typing import Dict, Literal, Tuple, List, Any

from utils import load
from utils.llm_client import responser, extract_content
from prompt.evaluate_prompt import EVALUATE_PROMPT
import random


class QuickExecute:
    """
    完成不同数据集的评估。
    """

    def __init__(self, prompt: str, k: int = 3, model=None):

        self.prompt = prompt
        self.k = k
        self.model = model

    async def prompt_execute(self) -> tuple[Any]:
        _, _, qa, _ = load.load_meta_data(k=self.k)
        answers = []

        async def fetch_answer(q: str) -> Dict[str, Any]:
            messages = [{"role": "user", "content": f"{self.prompt}\n\n{q}"}]
            try:
                answer = await responser(messages, model=self.model['name'], temperature=self.model['temperature'])
                return {'question': q, 'answer': answer.content}
            except Exception as e:
                return {'question': q, 'answer': str(e)}

        tasks = [fetch_answer(item['question']) for item in qa]
        answers = await asyncio.gather(*tasks)

        return answers


class QuickEvaluate:
    """
    Complete the evaluation for different datasets here.
    """

    def __init__(self, k: int = 3):
        self.k = k

    async def prompt_evaluate(self, sample: list, new_sample: list, model: dict) -> bool:
        _, requirement, qa, _ = load.load_meta_data(k=self.k)

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
            response = await responser(messages, model=model['name'], temperature=model['temperature'])
            choose = extract_content(response.content, 'choose')

            if is_swapped:
                return choose == "A"
            return choose == "B"

        except Exception as e:
            print(e)
            return False



if __name__ == "__main__":
    execute = QuickExecute(prompt="Answer the Question，{question}", k=3)

    # 使用asyncio.run来运行异步方法
    answers = asyncio.run(execute.prompt_evaluate())
    print(answers)

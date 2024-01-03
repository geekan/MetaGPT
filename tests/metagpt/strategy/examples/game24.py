# -*- coding: utf-8 -*-
# @Date    : 12/25/2023 1:36 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import re
from typing import Dict

from metagpt.strategy.tot import TreeofThought
from metagpt.strategy.tot_schema import (
    BaseEvaluator,
    BaseParser,
    Strategy,
    ThoughtSolverConfig,
)
from tests.metagpt.strategy.prompt_templates.game24 import propose_prompt, value_prompt


class Game24Parser(BaseParser):
    propose_prompt: str = propose_prompt
    value_prompt: str = value_prompt

    def __call__(self, input_text: str) -> str:
        last_line = input_text.strip().split("\n")[-1]
        return last_line.split("left: ")[-1].split(")")[0]

    def propose(self, current_state: str, **kwargs) -> str:
        return self.propose_prompt.format(input=current_state, **kwargs)

    def value(self, input: str = "", **kwargs) -> str:
        node_result = self(input)
        return self.value_prompt.format(input=node_result)


class Game24Evaluator(BaseEvaluator):
    value_map: Dict[str, float] = {"impossible": 0.001, "likely": 1, "sure": 20}  # TODO: ad hoc
    status_map: Dict = {val: key for key, val in value_map.items()}

    def __call__(self, evaluation: str, **kwargs) -> float:
        try:
            matches = re.findall(r"\b(impossible|sure|likely)\b", evaluation)
            value = self.value_map[matches[0]]
        except:
            value = 0.001
        return value

    def status_verify(self, value):
        status = False
        if value in self.status_map:
            status_value = self.status_map[value]
            if status_value != "impossible":
                status = True
        return status


def test_game24():
    import asyncio

    initial_prompt = """4 5 6 10"""
    parser = Game24Parser()
    evaluator = Game24Evaluator()

    config = ThoughtSolverConfig(n_generate_sample=5, parser=parser, evaluator=evaluator)

    tot = TreeofThought(strategy=Strategy.BFS, config=config)
    asyncio.run(tot.solve(init_prompt=initial_prompt))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : evaluate_action.py
@Desc    : The implementation of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
from typing import Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser, general_after_log, to_markdown_code_block


class EvaluationData(BaseModel):
    """Model to represent evaluation data.

    Attributes:
        is_pass (bool): Indicates if the evaluation passed or failed.
        conclusion (Optional[str]): Conclusion or remarks about the evaluation.
    """

    is_pass: bool
    conclusion: Optional[str] = None


class EvaluateAction(Action):
    """The base class for an evaluation action.

    This class provides methods to evaluate prompts using a specified language model.
    """

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _evaluate(self, prompt: str) -> (bool, str):
        """Evaluates a given prompt.

        Args:
            prompt (str): The prompt to be evaluated.

        Returns:
            tuple: A tuple containing:
                - bool: Indicates if the evaluation passed.
                - str: The JSON string containing the evaluation data.
        """
        rsp = await self.llm.aask(prompt)
        json_data = CodeParser.parse_code(text=rsp, lang="json")
        data = EvaluationData.model_validate_json(json_data)
        return data.is_pass, to_markdown_code_block(val=json_data, type_="json")

    async def _vote(self, prompt: str) -> EvaluationData:
        """Evaluates a prompt multiple times and returns the consensus.

        Args:
            prompt (str): The prompt to be evaluated.

        Returns:
            EvaluationData: An object containing the evaluation result and a summary of evaluations.
        """
        evaluations = {}
        for i in range(3):
            vote, evaluation = await self._evaluate(prompt)
            val = evaluations.get(vote, [])
            val.append(evaluation)
            if len(val) > 1:
                return EvaluationData(is_pass=vote, conclusion="\n".join(val))
            evaluations[vote] = val

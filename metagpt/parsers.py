#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 21:51
@Author  : alexanderwu
@File    : parsers.py
"""

import re
from typing import Union
from metagpt.logs import logger
from langchain.schema import AgentAction, AgentFinish, OutputParserException

FINAL_ANSWER_ACTION = "Final Answer:"


class BasicParser:
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        if FINAL_ANSWER_ACTION in text:
            return AgentFinish(
                {"output": text.split(FINAL_ANSWER_ACTION)[-1].strip()}, text
            )
        # \s matches against tab/newline/whitespace
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        )
        match = re.search(regex, text, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(action, action_input.strip(" ").strip('"'), text)


if __name__ == '__main__':
    parser = BasicParser()
    action_sample = "I need to calculate the 0.23 power of Elon Musk's current age.\nAction: Calculator\nAction Input: 49 raised to the 0.23 power"
    final_answer_sample = "I now know the answer to the question.\nFinal Answer: 2.447626228522259"

    rsp = parser.parse(action_sample)
    logger.info(rsp)

    rsp = parser.parse(final_answer_sample)
    logger.info(rsp)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/26 20:54
@Author  : alexanderwu
@File    : test_parser.py
"""
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from metagpt.parsers import BasicParser

def test_basic_parser():
    parser = BasicParser()
    action_sample = "I need to calculate the 0.23 power of Elon Musk's current age.\nAction: Calculator\nAction Input: 49 raised to the 0.23 power"
    final_answer_sample = "I now know the answer to the question.\nFinal Answer: 2.447626228522259"

    rsp = parser.parse(action_sample)
    assert isinstance(rsp, AgentAction)

    rsp = parser.parse(final_answer_sample)
    assert isinstance(rsp, AgentFinish)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/19 15:02
@Author  : DevXiaolan
@File    : prepare_interview.py
"""
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode

QUESTIONS = ActionNode(
    key="Questions",
    expected_type=list[str],
    instruction="""Role: You are an interviewer of our company who is well-knonwn in frontend or backend develop;
Requirement: Provide a list of questions for the interviewer to ask the interviewee, by reading the resume of the interviewee in the context.
Attention: Provide as markdown block as the format above, at least 10 questions.""",
    example=["1. What ...", "2. How ..."],
)


class PrepareInterview(Action):
    name: str = "PrepareInterview"

    async def run(self, context):
        return await QUESTIONS.fill(context=context, llm=self.llm)

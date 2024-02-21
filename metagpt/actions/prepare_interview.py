#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/19 15:02
# @Author  : DevXiaolan
# @File    : prepare_interview.py

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
    """Prepares an interview by generating a list of questions.

    This class is responsible for preparing an interview by generating a list of questions
    based on the resume of the interviewee. It utilizes an ActionNode to define the requirements
    and format for the questions.

    Attributes:
        name: A string indicating the name of the action.
    """

    name: str = "PrepareInterview"

    async def run(self, context):
        """Generates a list of interview questions based on the interviewee's resume.

        Args:
            context: The context containing the interviewee's resume.

        Returns:
            A list of formatted interview questions.
        """
        return await QUESTIONS.fill(context=context, llm=self.llm)

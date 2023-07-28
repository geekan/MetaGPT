#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/27
@Author  : mashenquan
@File    : write_teaching_plan.py
"""
from langchain.llms.base import LLM
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.schema import Message


class TeachingPlanRequirement(Action):
    """Teaching Plan Requirement without any implementation details"""

    async def run(self, *args, **kwargs):
        raise NotImplementedError


class WriteTeachingPlanPart(Action):
    """Write Teaching Plan Part"""

    def __init__(self, name: str = '', context=None, llm: LLM = None, topic="", language="Chinese"):
        """

        Args:
            name: action name
            context: context
            llm: object of :class:`LLM`
            topic: topic part of teaching plan
        """
        super().__init__(name, context, llm)
        self.topic = topic
        self.language = language
        self.rsp = None

    async def run(self, *args, **kwargs):
        if len(args) < 1 or len(args[0]) < 1 or not isinstance(args[0][0], Message):
            raise ValueError("Invalid args, a tuple of List[Message] is expected")

        statements = self.TOPIC_STATEMENTS.get(self.topic, [])
        formatter = self.PROMPT_TITLE_TEMPLATE if self.topic == self.COURSE_TITLE else self.PROMPT_TEMPLATE
        prompt = formatter.format(formation=self.FORMATION,
                                  role=self.prefix,
                                  statements="\n".join(statements),
                                  lesson=args[0][0].content,
                                  topic=self.topic,
                                  language=self.language)

        logger.debug(prompt)
        rsp = await self._aask(prompt=prompt)
        logger.debug(rsp)
        self._set_result(rsp)
        return self.rsp

    def _set_result(self, rsp):
        if self.DATA_BEGIN_TAG in rsp:
            ix = rsp.index(self.DATA_BEGIN_TAG)
            rsp = rsp[ix + len(self.DATA_BEGIN_TAG):]
        if self.DATA_END_TAG in rsp:
            ix = rsp.index(self.DATA_END_TAG)
            rsp = rsp[0:ix]
        self.rsp = rsp.strip()
        if self.topic != self.COURSE_TITLE:
            return
        if '#' not in self.rsp or self.rsp.index('#') != 0:
            self.rsp = "# " + self.rsp

    def __str__(self):
        """Return `topic` value when str()"""
        return self.topic

    def __repr__(self):
        """Show `topic` value when debug"""
        return self.topic

    FORMATION = """
    \t\"Capacity and role\" defines the role you are currently playing;
    \t\"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags enclose the content of textbook;
    \t\"Statement\" defines the work detail you need to complete at this stage;
    \t\"Answer options\" defines the format requirements for your responses;
    \t\"Constraint\" defines the conditions that your responses must comply with.
    """
    COURSE_TITLE = "Title"
    TOPICS = [COURSE_TITLE, "Teaching Hours", "Teaching Objectives", "Teaching Content",
              "Teaching Methods and Strategies", "Learning Activities",
              "Teaching Time Allocation", "Assessment and Feedback", "Teaching Summary and Improvement"]

    TOPIC_STATEMENTS = {
        COURSE_TITLE: ["Statement: Find and return the title of the lesson only in markdown first-level header format, "
                       "without anything else."],
        "Teaching Content": [
            "Statement: \"Teaching Content\" must include vocabulary, analysis, and examples of various grammar "
            "structures that appear in the textbook, as well as the listening materials and key points.",
            "Statement: \"Teaching Content\" must include more examples."],
        "Teaching Time Allocation": [
            "Statement: \"Teaching Time Allocation\" must include how much time is allocated to each "
            "part of the textbook content."],
        "Teaching Methods and Strategies": [
            "Statement: \"Teaching Methods and Strategies\" must include teaching focus, difficulties, materials, "
            "procedures, in detail."
        ]
    }

    # Teaching plan title
    PROMPT_TITLE_TEMPLATE = """
        Do not refer to the context of the previous conversation records, start the conversation anew.\n\n
        Formation: {formation}\n\n
        {statements}\n
        Constraint: Writing in {language}.\n
        Answer options: Encloses the lesson title with "[TEACHING_PLAN_BEGIN]" and "[TEACHING_PLAN_END]" tags.\n
        [LESSON_BEGIN]\n
        {lesson}\n
        [LESSON_END]
        """

    # Teaching plan parts:
    PROMPT_TEMPLATE = """
    Do not refer to the context of the previous conversation records, start the conversation anew.\n\n
    Formation: {formation}\n\n
    Capacity and role: {role}\n
    Statement: Write the "{topic}" part of teaching plan, WITHOUT ANY content unrelated to "{topic}"!!\n
    {statements}\n
    Answer options: Enclose the teaching plan content with "[TEACHING_PLAN_BEGIN]" and "[TEACHING_PLAN_END]" tags.\n
    Answer options: Using proper markdown format from second-level header format.\n
    Constraint: Writing in {language}.\n
    [LESSON_BEGIN]\n
    {lesson}\n
    [LESSON_END]
    """

    DATA_BEGIN_TAG = "[TEACHING_PLAN_BEGIN]"
    DATA_END_TAG = "[TEACHING_PLAN_END]"

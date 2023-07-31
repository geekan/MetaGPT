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

        statement_patterns = self.TOPIC_STATEMENTS.get(self.topic, [])
        statements = []
        from metagpt.roles import Role
        for p in statement_patterns:
            s = Role.format_value(p, kwargs)
            statements.append(s)
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

    FORMATION = "\"Capacity and role\" defines the role you are currently playing;\n" \
                "\t\"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags enclose the content of textbook;\n" \
                "\t\"Statement\" defines the work detail you need to complete at this stage;\n" \
                "\t\"Answer options\" defines the format requirements for your responses;\n" \
                "\t\"Constraint\" defines the conditions that your responses must comply with."

    COURSE_TITLE = "Title"
    TOPICS = [COURSE_TITLE, "Teaching Hours", "Teaching Objectives", "Teaching Content",
              "Teaching Methods and Strategies", "Learning Activities",
              "Teaching Time Allocation", "Assessment and Feedback", "Teaching Summary and Improvement",
              "Vocabulary Practice", "Grammar Practice", "Reading Comprehension", "Listening Practice",
              "Writing Practice", "Speaking Practice", "Translation Practice", "Listening and Speaking Activities"]

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
        ],
        "Vocabulary Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create vocabulary practice exercises. The exercises should be in either {language} with "
            "{teaching_language} answers or {teaching_language} with {language} answers. The key-related vocabulary "
            "and phrases in the textbook content must all be included in the exercises."
        ],
        "Grammar Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create grammar practice exercises. "],
        "Reading Comprehension": [
            "Statement: Based on the vocabulary of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create {teaching_language} reading comprehension exercises. ",
            "Statement: Prohibit the use of words that are not within the scope of the \"[LESSON_BEGIN]\" "
            "and \"[LESSON_END]\" tags.",
            "Statement: Prohibit copy the content of the \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags.",
            "Answer options: Write the story content in {teaching_language}."
        ],
        "Listening Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create listening practice exercises. Each exercise should include the audio content and the "
            "question-and-answer part."
        ],
        "Writing Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create writing practice exercises.",
            #"Statement: Prohibit using content not related to \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags.",
            "Statement: Prohibit copying the content enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags."
        ],
        "Speaking Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create speaking practice exercises.",
            #"Statement: Prohibit using content not related to \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags.",
            "Statement: Prohibit copying the content enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags."
        ],
        "Translation Practice": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create Translation practice exercises.",
            #"Statement: Prohibit using content not related to \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags.",
            "Statement: Prohibit copying the content enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags."
        ],
        "Listening and Speaking Activities": [
            "Statement: Based on the content of the textbook enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\", "
            "create listening and speaking activities exercises.",
            #"Statement: Prohibit using content not related to \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags.",
            "Statement: Prohibit copying the content enclosed by \"[LESSON_BEGIN]\" and \"[LESSON_END]\" tags."
        ]
    }

    # Teaching plan title
    PROMPT_TITLE_TEMPLATE = "Do not refer to the context of the previous conversation records, " \
                            "start the conversation anew.\n\n" \
                            "Formation: {formation}\n\n" \
                            "{statements}\n" \
                            "Constraint: Writing in {language}.\n" \
                            "Answer options: Encloses the lesson title with \"[TEACHING_PLAN_BEGIN]\" " \
                            "and \"[TEACHING_PLAN_END]\" tags.\n" \
                            "[LESSON_BEGIN]\n" \
                            "{lesson}\n" \
                            "[LESSON_END]"

    # Teaching plan parts:
    PROMPT_TEMPLATE = "Do not refer to the context of the previous conversation records, " \
                      "start the conversation anew.\n\n" \
                      "Formation: {formation}\n\n" \
                      "Capacity and role: {role}\n" \
                      "Statement: Write the \"{topic}\" part of teaching plan, " \
                      "WITHOUT ANY content unrelated to \"{topic}\"!!\n" \
                      "{statements}\n" \
                      "Answer options: Enclose the teaching plan content with \"[TEACHING_PLAN_BEGIN]\" " \
                      "and \"[TEACHING_PLAN_END]\" tags.\n" \
                      "Answer options: Using proper markdown format from second-level header format.\n" \
                      "Constraint: Writing in {language}.\n" \
                      "[LESSON_BEGIN]\n" \
                      "{lesson}\n" \
                      "[LESSON_END]"

    DATA_BEGIN_TAG = "[TEACHING_PLAN_BEGIN]"
    DATA_END_TAG = "[TEACHING_PLAN_END]"

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/27
@Author  : mashenquan
@File    : write_teaching_plan.py
"""
from typing import Optional

from metagpt.actions import Action
from metagpt.context import Context
from metagpt.logs import logger


class WriteTeachingPlanPart(Action):
    """Write Teaching Plan Part"""

    i_context: Optional[str] = None
    topic: str = ""
    language: str = "Chinese"
    rsp: Optional[str] = None

    async def run(self, with_message=None, **kwargs):
        statement_patterns = TeachingPlanBlock.TOPIC_STATEMENTS.get(self.topic, [])
        statements = []
        for p in statement_patterns:
            s = self.format_value(p, context=self.context)
            statements.append(s)
        formatter = (
            TeachingPlanBlock.PROMPT_TITLE_TEMPLATE
            if self.topic == TeachingPlanBlock.COURSE_TITLE
            else TeachingPlanBlock.PROMPT_TEMPLATE
        )
        prompt = formatter.format(
            formation=TeachingPlanBlock.FORMATION,
            role=self.prefix,
            statements="\n".join(statements),
            lesson=self.i_context,
            topic=self.topic,
            language=self.language,
        )

        logger.debug(prompt)
        rsp = await self._aask(prompt=prompt)
        logger.debug(rsp)
        self._set_result(rsp)
        return self.rsp

    def _set_result(self, rsp):
        if TeachingPlanBlock.DATA_BEGIN_TAG in rsp:
            ix = rsp.index(TeachingPlanBlock.DATA_BEGIN_TAG)
            rsp = rsp[ix + len(TeachingPlanBlock.DATA_BEGIN_TAG) :]
        if TeachingPlanBlock.DATA_END_TAG in rsp:
            ix = rsp.index(TeachingPlanBlock.DATA_END_TAG)
            rsp = rsp[0:ix]
        self.rsp = rsp.strip()
        if self.topic != TeachingPlanBlock.COURSE_TITLE:
            return
        if "#" not in self.rsp or self.rsp.index("#") != 0:
            self.rsp = "# " + self.rsp

    def __str__(self):
        """Return `topic` value when str()"""
        return self.topic

    def __repr__(self):
        """Show `topic` value when debug"""
        return self.topic

    @staticmethod
    def format_value(value, context: Context):
        """Fill parameters inside `value` with `options`."""
        if not isinstance(value, str):
            return value
        if "{" not in value:
            return value

        options = context.config.model_dump()
        for k, v in context.kwargs:
            options[k] = v  # None value is allowed to override and disable the value from config.
        opts = {k: v for k, v in options.items() if v is not None}
        try:
            return value.format(**opts)
        except KeyError as e:
            logger.warning(f"Parameter is missing:{e}")

        for k, v in opts.items():
            value = value.replace("{" + f"{k}" + "}", str(v))
        return value


class TeachingPlanBlock:
    FORMATION = (
        '"Capacity and role" defines the role you are currently playing;\n'
        '\t"[LESSON_BEGIN]" and "[LESSON_END]" tags enclose the content of textbook;\n'
        '\t"Statement" defines the work detail you need to complete at this stage;\n'
        '\t"Answer options" defines the format requirements for your responses;\n'
        '\t"Constraint" defines the conditions that your responses must comply with.'
    )

    COURSE_TITLE = "Title"
    TOPICS = [
        COURSE_TITLE,
        "Teaching Hours",
        "Teaching Objectives",
        "Teaching Content",
        "Teaching Methods and Strategies",
        "Learning Activities",
        "Teaching Time Allocation",
        "Assessment and Feedback",
        "Teaching Summary and Improvement",
        "Vocabulary Cloze",
        "Choice Questions",
        "Grammar Questions",
        "Translation Questions",
    ]

    TOPIC_STATEMENTS = {
        COURSE_TITLE: [
            "Statement: Find and return the title of the lesson only in markdown first-level header format, "
            "without anything else."
        ],
        "Teaching Content": [
            'Statement: "Teaching Content" must include vocabulary, analysis, and examples of various grammar '
            "structures that appear in the textbook, as well as the listening materials and key points.",
            'Statement: "Teaching Content" must include more examples.',
        ],
        "Teaching Time Allocation": [
            'Statement: "Teaching Time Allocation" must include how much time is allocated to each '
            "part of the textbook content."
        ],
        "Teaching Methods and Strategies": [
            'Statement: "Teaching Methods and Strategies" must include teaching focus, difficulties, materials, '
            "procedures, in detail."
        ],
        "Vocabulary Cloze": [
            'Statement: Based on the content of the textbook enclosed by "[LESSON_BEGIN]" and "[LESSON_END]", '
            "create vocabulary cloze. The cloze should include 10 {language} questions with {teaching_language} "
            "answers, and it should also include 10 {teaching_language} questions with {language} answers. "
            "The key-related vocabulary and phrases in the textbook content must all be included in the exercises.",
        ],
        "Grammar Questions": [
            'Statement: Based on the content of the textbook enclosed by "[LESSON_BEGIN]" and "[LESSON_END]", '
            "create grammar questions. 10 questions."
        ],
        "Choice Questions": [
            'Statement: Based on the content of the textbook enclosed by "[LESSON_BEGIN]" and "[LESSON_END]", '
            "create choice questions. 10 questions."
        ],
        "Translation Questions": [
            'Statement: Based on the content of the textbook enclosed by "[LESSON_BEGIN]" and "[LESSON_END]", '
            "create translation questions. The translation should include 10 {language} questions with "
            "{teaching_language} answers, and it should also include 10 {teaching_language} questions with "
            "{language} answers."
        ],
    }

    # Teaching plan title
    PROMPT_TITLE_TEMPLATE = (
        "Do not refer to the context of the previous conversation records, "
        "start the conversation anew.\n\n"
        "Formation: {formation}\n\n"
        "{statements}\n"
        "Constraint: Writing in {language}.\n"
        'Answer options: Encloses the lesson title with "[TEACHING_PLAN_BEGIN]" '
        'and "[TEACHING_PLAN_END]" tags.\n'
        "[LESSON_BEGIN]\n"
        "{lesson}\n"
        "[LESSON_END]"
    )

    # Teaching plan parts:
    PROMPT_TEMPLATE = (
        "Do not refer to the context of the previous conversation records, "
        "start the conversation anew.\n\n"
        "Formation: {formation}\n\n"
        "Capacity and role: {role}\n"
        'Statement: Write the "{topic}" part of teaching plan, '
        'WITHOUT ANY content unrelated to "{topic}"!!\n'
        "{statements}\n"
        'Answer options: Enclose the teaching plan content with "[TEACHING_PLAN_BEGIN]" '
        'and "[TEACHING_PLAN_END]" tags.\n'
        "Answer options: Using proper markdown format from second-level header format.\n"
        "Constraint: Writing in {language}.\n"
        "[LESSON_BEGIN]\n"
        "{lesson}\n"
        "[LESSON_END]"
    )

    DATA_BEGIN_TAG = "[TEACHING_PLAN_BEGIN]"
    DATA_END_TAG = "[TEACHING_PLAN_END]"

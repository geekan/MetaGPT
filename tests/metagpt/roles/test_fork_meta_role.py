#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/8
@Author  : mashenquan
@File    : test_fork_meta_role.py
"""
from typing import Dict

from pydantic import BaseModel

from metagpt.roles.fork_meta_role import ForkMetaRole


def test_creat_role():
    class Inputs(BaseModel):
        role: Dict
        action_count: int

    inputs = [
        {
            "role": {
                "role_type": "fork",
                "name": "Lily",
                "profile": "{teaching_language} Teacher",
                "goal": "writing a {language} teaching plan part by part",
                "constraints": "writing in {language}",
                "role": "You are a {teaching_language} Teacher, named Lily, your goal is writing a {"
                        "teaching_language} teaching plan part by part, and the constraint is writing in {language}.",
                "desc": "",
                "output_filename": "teaching_plan_demo.md",
                "requirement": ["TeachingPlanRequirement"],
                "templates": [
                    "Do not refer to the context of the previous conversation records, start the conversation "
                    "anew.\n\nFormation: \"Capacity and role\" defines the role you are currently playing;\n\t\"["
                    "LESSON_BEGIN]\" and \"[LESSON_END]\" tags enclose the content of textbook;\n\t\"Statement\" "
                    "defines the work detail you need to complete at this stage;\n\t\"Answer options\" defines the "
                    "format requirements for your responses;\n\t\"Constraint\" defines the conditions that your "
                    "responses must comply with.\n\n{statements}\nConstraint: Writing in {language}.\nAnswer options: "
                    "Encloses the lesson title with \"[TEACHING_PLAN_BEGIN]\" and \"[TEACHING_PLAN_END]\" tags.\n["
                    "LESSON_BEGIN]\n{lesson}\n[LESSON_END]",
                    "Do not refer to the context of the previous conversation records, start the conversation "
                    "anew.\n\nFormation: \"Capacity and role\" defines the role you are currently playing;\n\t\"["
                    "LESSON_BEGIN]\" and \"[LESSON_END]\" tags enclose the content of textbook;\n\t\"Statement\" "
                    "defines the work detail you need to complete at this stage;\n\t\"Answer options\" defines the "
                    "format requirements for your responses;\n\t\"Constraint\" defines the conditions that your "
                    "responses must comply with.\n\nCapacity and role: {role}\nStatement: Write the \"{topic}\" part "
                    "of teaching plan, WITHOUT ANY content unrelated to \"{topic}\"!!\n{statements}\nAnswer options: "
                    "Enclose the teaching plan content with \"[TEACHING_PLAN_BEGIN]\" and \"[TEACHING_PLAN_END]\" "
                    "tags.\nAnswer options: Using proper markdown format from second-level header "
                    "format.\nConstraint: Writing in {language}.\n[LESSON_BEGIN]\n{lesson}\n[LESSON_END] "
                ],
                "actions": [
                    {
                        "name": "",
                        "topic": "Title",
                        "language": "Chinese",
                        "statements": [
                            "Statement: Find and return the title of the lesson only with \"# \" prefixed, without "
                            "anything else."],
                        "template_ix": 0},
                    {
                        "name": "",
                        "topic": "Teaching Hours",
                        "language": "Chinese",
                        "statements": [],
                        "template_ix": 1,
                        "rsp_begin_tag": "[TEACHING_PLAN_BEGIN]",
                        "rsp_end_tag": "[TEACHING_PLAN_END]"}
                ]
            },
            "action_count": 2
        }
    ]

    for i in inputs:
        seed = Inputs(**i)
        kwargs = {
            "teaching_language": "AA",
            "language": "BB"
        }
        role = ForkMetaRole(seed.role, **kwargs)
        assert role.action_count == 2
        assert "{" not in role.profile
        assert "{" not in role.goal
        assert "{" not in role.constraints


if __name__ == '__main__':
    test_creat_role()

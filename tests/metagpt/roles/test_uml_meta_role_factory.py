#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/8
@Author  : mashenquan
@File    : test_uml_meta_role_factory.py
"""
from typing import List, Dict

from pydantic import BaseModel

from metagpt.roles.uml_meta_role_factory import UMLMetaRoleFactory


def test_create_roles():
    class Inputs(BaseModel):
        roles: List
        kwargs: Dict

    inputs = [
        {
            "roles": [
                {
                    "role_type": "fork",
                    "name": "Lily",
                    "profile": "{teaching_language} Teacher",
                    "goal": "writing a {language} teaching plan part by part",
                    "constraints": "writing in {language}",
                    "role": "You are a {teaching_language} Teacher, named Lily.",
                    "desc": "",
                    "output_filename": "teaching_plan_demo.md",
                    "requirement": ["TeachingPlanRequirement"],
                    "templates": ["Do 1 {statements}", "Do 2 {statements}"],
                    "actions": [
                        {
                            "name": "",
                            "topic": "Title",
                            "language": "Chinese",
                            "statements": ["statement 1", "statement 2"]}
                    ],
                    "template_ix": 0
                }
            ],
            "kwargs": {
                "teaching_language": "AA",
                "language": "BB",
            }
        }
    ]

    for i in inputs:
        seed = Inputs(**i)
        roles = UMLMetaRoleFactory.create_roles(seed.roles, **seed.kwargs)
        assert len(roles) == 1
        assert "{" not in roles[0].profile
        assert "{" not in roles[0].goal
        assert roles[0].action_count == 1


if __name__ == '__main__':
    test_create_roles()

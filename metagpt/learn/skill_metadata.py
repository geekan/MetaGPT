#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/20
@Author  : mashenquan
@File    : skill_metadata.py
@Desc    : Defines metadata for the `skill`.
        Depending on the context and specific circumstances, skills may have different effects.
        For example:
            Proprietor: "Skill of the proprietor entity."
            Holder: "Skill of the holder entity."
            Possessor: "Skill of the possessor entity."
            Controller: "Skill of the controller entity."
            Owner: "Skill of the owner entity."
"""


def skill_metadata(name, description, requisite):
    def decorator(func):
        func.skill_name = name
        func.skill_description = description
        func.skill_requisite = requisite
        return func

    return decorator

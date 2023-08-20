#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/20
@Author  : mashenquan
@File    : skill_metadata.py
@Desc    : Defines metadata for the `skill`.
        Depending on the context and specific circumstances, skills may have different effects.
        For example:
            Proprietor: "Skill of the proprietor entity."（所有者的技能）
            Holder: "Skill of the holder entity."（持有者的技能）
            Possessor: "Skill of the possessor entity."（拥有者的技能）
            Controller: "Skill of the controller entity."（控制者的技能）
            Owner: "Skill of the owner entity."（所有者的技能）
"""


def skill_metadata(name, description, requisite):
    def decorator(func):
        func.skill_name = name
        func.skill_description = description
        func.skill_requisite = requisite
        return func

    return decorator

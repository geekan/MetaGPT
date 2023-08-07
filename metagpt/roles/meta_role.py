#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : meta_role.py
@Desc   : 我试图将UML的一些符号概念引入到MetaGPT，使其具备通过符号拼接自由搭建flow的能力。同时我也尝试将这些符号做得配置化和标准化，让flow搭建流程更便捷。
        分工参照UML 2.0 activity diagrams: `https://www.uml-diagrams.org/activity-diagrams.html`
"""
from typing import Dict, List

from metagpt.roles import Role
from pydantic import BaseModel

class UMLMetaRoleArgs(BaseModel):
    role_type: str
    name: str = ""
    profile: str = ""
    goal: str = ""
    constraints: str = ""
    desc: str = ""
    actions: List

class UMLMetaRole(Role):
    """UML activity roles抽象父类"""

    def __init__(self, role_args: Dict):
        """"""
        self.role_args

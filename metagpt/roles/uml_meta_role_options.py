#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : uml_meta_role_options.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
"""

from typing import List, Dict

from pydantic import BaseModel


# `startup` field of config/pattern/template.yaml
class StartupConfig(BaseModel):
    requirement: str
    role: str
    investment: float = 3.0
    n_round: int = 3


# config/pattern/template.yaml
class ProjectConfig(BaseModel):
    startup: StartupConfig
    roles: List[Dict]


# element of `actions` field of config/pattern/template.yaml
class MetaActionOptions(BaseModel):
    topic: str
    name: str = ""
    language: str = "Chinese"
    template_ix: int = 0
    statements: List[str] = []
    template: str = ""
    rsp_begin_tag: str = ""
    rsp_end_tag: str = ""

    def set_default_template(self, v):
        if not self.template:
            self.template = v

    def format_prompt(self, **kwargs):
        statements = "\n".join(self.statements)
        opts = kwargs.copy()
        opts["statements"] = statements

        from metagpt.roles import Role
        prompt = Role.format_value(self.template, opts)
        return prompt


# element of `roles` field of config/pattern/template.yaml
class UMLMetaRoleOptions(BaseModel):
    role_type: str
    name: str = ""
    profile: str = ""
    goal: str = ""
    role: str = ""
    constraints: str = ""
    desc: str = ""
    templates: List[str] = []
    output_filename: str = ""
    actions: List
    requirement: List

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/8
@Author  : mashenquan
@File    : test_uml_meta_role_options.py
"""
from typing import List

from pydantic import BaseModel

from metagpt.roles.uml_meta_role_options import MetaActionOptions


def test_set_default_template():
    class Inputs(BaseModel):
        statements: List
        template: str
        expect_prompt: str

    inputs = [
        {
            "statements": ["Statement: 1", "Statement: 2"],
            "template": "{statements}",
            "expect_prompt": "Statement: 1\nStatement: 2"
        }
    ]

    for i in inputs:
        seed = Inputs(**i)
        opt = MetaActionOptions(topic="", statements=seed.statements)
        assert opt.template == ""
        opt.set_default_template(seed.template)
        assert opt.template == seed.template
        kwargs = {}
        assert opt.format_prompt(**kwargs) == seed.expect_prompt


if __name__ == '__main__':
    test_set_default_template()

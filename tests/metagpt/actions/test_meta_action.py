#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/8
@Author  : mashenquan
@File    : test_meta_action.py
"""
from typing import Dict

from pydantic import BaseModel

from metagpt.actions.meta_action import MetaAction
from metagpt.roles.uml_meta_role_options import MetaActionOptions


def test_meta_action_create():
    class Inputs(BaseModel):
        options: Dict
        kwargs: Dict
        expect_class_name: str
        expect_prompt: str

    inputs = [
        {
            "options": {
                "topic": "TOPIC_A",
                "name": "A",
                "language": "XX",
                "template_ix": 0,
                "statements": ["Statement A", "Statement B"],
                "template": "{statements}",
                "rsp_begin_tag": "",
                "rsp_end_tag": ""
            },
            "kwargs": {},
            "expect_class_name": "TOPIC_A",
            "expect_prompt": "\n".join(["Statement A", "Statement B"]),
        }
    ]

    for i in inputs:
        seed = Inputs(**i)
        opt = MetaActionOptions(**seed.options)
        act = MetaAction(opt, **seed.kwargs)
        assert seed.expect_prompt == act.prompt
        t = MetaAction.get_action_type(seed.expect_class_name)
        assert t.__name__ == seed.expect_class_name


if __name__ == '__main__':
    test_meta_action_create()

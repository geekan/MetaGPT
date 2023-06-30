#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:44
@Author  : alexanderwu
@File    : test_role.py
"""
from metagpt.roles import Role


def test_role_desc():
    i = Role(profile='Sales', desc='Best Seller')
    assert i.profile == 'Sales'
    assert i._setting.desc == 'Best Seller'

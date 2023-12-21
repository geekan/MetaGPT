#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of Role

from metagpt.roles.role import Role


def test_role_desc():
    role = Role(profile="Sales", desc="Best Seller")
    assert role.profile == "Sales"
    assert role._setting.desc == "Best Seller"

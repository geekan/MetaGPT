#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of Role
import pytest

from metagpt.roles.role import Role


def test_role_desc():
    role = Role(profile="Sales", desc="Best Seller")
    assert role.profile == "Sales"
    assert role.desc == "Best Seller"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

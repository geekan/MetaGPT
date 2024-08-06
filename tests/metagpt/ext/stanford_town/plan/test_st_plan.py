#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of st_plan


import pytest

from metagpt.ext.stanford_town.plan.st_plan import _choose_retrieved, _should_react
from tests.metagpt.ext.stanford_town.plan.test_conversation import init_two_roles


@pytest.mark.asyncio
async def test_should_react():
    role_ir, role_km = await init_two_roles()
    roles = {role_ir.name: role_ir, role_km.name: role_km}
    role_ir.scratch.act_address = "mock data"

    observed = await role_ir.observe()
    retrieved = role_ir.retrieve(observed)

    focused_event = _choose_retrieved(role_ir.name, retrieved)

    if focused_event:
        reaction_mode = await _should_react(role_ir, focused_event, roles)  # chat with Isabella Rodriguez
        assert not reaction_mode

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of st_plan

import pytest

from metagpt.ext.stanford_town.plan.st_plan import (
    _choose_retrieved,
    _should_react,
    _wait_react,
)
from tests.metagpt.ext.stanford_town.plan.test_conversation import init_two_roles


def test_should_react():
    role_ir, role_km = init_two_roles()
    roles = {role_ir.name: role_ir, role_km.name: role_km}

    observed = role_ir.observe()
    retrieved = role_ir.retrieve(observed)

    focused_event = _choose_retrieved(role_ir.name, retrieved)

    if focused_event:
        reaction_mode = _should_react(role_ir, focused_event, roles)  # chat with Isabella Rodriguez
        assert "chat with" in reaction_mode


@pytest.mark.asyncio
async def test_wait_react():
    role_ir, role_km = init_two_roles("base_the_ville_isabella_maria_klaus")
    reaction_mode = "wait: February 13, 2023, 00:01:30"
    f_daily_schedule = role_ir.scratch.f_daily_schedule
    # [['sleeping', 360], ['waking up and completing her morning routine (getting out of bed)', 5], ['sleeping', 180]]

    await _wait_react(role_ir, reaction_mode)
    new_f_daily_schedule = role_ir.scratch.f_daily_schedule
    # [['sleeping', 360], ['waking up and completing her morning routine (getting out of bed)', 5],
    # ['waking up and completing her morning routine (brushing her teeth)', 5], ['sleeping', 180]]
    assert len(f_daily_schedule) == len(new_f_daily_schedule)

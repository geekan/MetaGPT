#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of actions/summarize_conv

import pytest

from metagpt.ext.stanford_town.actions.summarize_conv import SummarizeConv


@pytest.mark.asyncio
async def test_summarize_conv():
    conv = [("Role_A", "what's the weather today?"), ("Role_B", "It looks pretty good, and I will take a walk then.")]

    output = await SummarizeConv().run(conv)
    assert "weather" in output

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of actions/summarize_conv

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "./../../../"))

from metagpt.logs import logger

from st_game.actions.summarize_conv import SummarizeConv


def test_summarize_conv():
    conv = [
        ("Role_A", "what's the weather today?"),
        ("Role_B", "It looks pretty good, and I will take a walk then.")
    ]

    output = SummarizeConv().run(conv)
    assert "weather" in output

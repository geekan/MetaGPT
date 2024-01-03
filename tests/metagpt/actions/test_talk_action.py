#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_talk_action.py
"""

import pytest

from metagpt.actions.talk_action import TalkAction
from metagpt.config import CONFIG
from metagpt.schema import Message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_description", "language", "context", "knowledge", "history_summary"),
    [
        (
            "mathematician",
            "English",
            "How old is Susie?",
            "Susie is a girl born in 2011/11/14. Today is 2023/12/3",
            "balabala... (useless words)",
        ),
        (
            "mathematician",
            "Chinese",
            "Does Susie have an apple?",
            "Susie is a girl born in 2011/11/14. Today is 2023/12/3",
            "Susie had an apple, and she ate it right now",
        ),
    ],
)
@pytest.mark.usefixtures("llm_mock")
async def test_prompt(agent_description, language, context, knowledge, history_summary):
    # Prerequisites
    CONFIG.agent_description = agent_description
    CONFIG.language = language

    action = TalkAction(context=context, knowledge=knowledge, history_summary=history_summary)
    assert "{" not in action.prompt
    assert "{" not in action.prompt_gpt4

    rsp = await action.run()
    assert rsp
    assert isinstance(rsp, Message)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

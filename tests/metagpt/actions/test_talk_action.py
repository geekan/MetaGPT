#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_talk_action.py
"""

import pytest

from metagpt.actions.talk_action import TalkAction
from metagpt.schema import Message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_description", "language", "talk_context", "knowledge", "history_summary"),
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
async def test_prompt(agent_description, language, talk_context, knowledge, history_summary, context):
    # Prerequisites
    context.kwargs.agent_description = agent_description
    context.kwargs.language = language

    action = TalkAction(i_context=talk_context, knowledge=knowledge, history_summary=history_summary, context=context)
    assert "{" not in action.prompt
    assert "{" not in action.prompt_gpt4

    rsp = await action.run()
    assert rsp
    assert isinstance(rsp, Message)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

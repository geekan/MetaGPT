#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script defines tools for dialog.
"""

from typing import List

from metagpt.actions.intent_detect import (
    IntentDetect,
    IntentDetectResult,
    LightIntentDetect,
)
from metagpt.context import Context
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["dialog", "intent detect"])
async def intent_detect(messages: List[Message]) -> IntentDetectResult:
    """Detects intent from a list of dialog messages.

    Args:
        messages (List[Message]): A list of dialog messages.

    Returns:
        IntentDetectResult: The result of intent detection.

    Example:
        >>> # Create messages
        >>> dialog = [
        >>>     {"role":"user", "content":"user queries ..."},
        >>>     {"role":"assistant", "content": "assistant answers ..."},
        >>>     ...
        >>> ]
        >>> from metagpt.schema import Message
        >>> messages = [Message.model_validate(i) for i in dialog]
        >>> result = await intent_detect(messages)
        >>> print(result.model_dump_json())
        {
            "clarifications": [
                {
                    "ref": "web app",
                    "clarification": "Could you provide more details about what you are looking to achieve with ...?"
                }
            ],
            "intentions": [
                {
                    "intention": {
                        "intent": "Request to build a service that can receive text messages and ...",
                        "refs": [
                            "Can you build TextToSummarize which is a SMS number that I can text ..."
                        ]
                    },
                    "sop": {
                        "description": "Intentions related to or including software development, such as ...",
                        "sop": [
                            "Writes a PRD based on software requirements.",
                            "Writes a design to the project repository, based on the PRD of the project.",
                            "Writes a project plan to the project repository, based on the design of the project.",
                            "Writes codes to the project repository, based on the project plan of the project.",
                            "Run QA test on the project repository.",
                            "Stage and commit changes for the project repository using Git."
                        ]
                    }
                },
                {
                    "intention": {
                        "intent": "Request for a phone number to send text messages for the summarization service",
                        "refs": []
                    },
                    "sop": null
                }
            ]
        }
    """
    ctx = Context()
    action = IntentDetect(context=ctx)
    await action.run(messages)
    return action.result


@register_tool(tags=["dialog", "software development intent detect"])
async def software_development_intent_detect(messages: List[Message]) -> IntentDetectResult:
    """Detects software development intent from a list of dialog messages.

    Args:
        messages (List[Message]): A list of dialog messages.

    Returns:
        IntentDetectResult: The result of intent detection.

    Example:
        >>> # Create messages
        >>> dialog = [
        >>>     {"role":"user", "content":"user queries ..."},
        >>>     {"role":"assistant", "content": "assistant answers ..."},
        >>>     ...
        >>> ]
        >>> from metagpt.schema import Message
        >>> messages = [Message.model_validate(i) for i in dialog]
        >>> result = await software_development_intent_detect(messages)
        >>> print(result)
        {
            "clarifications": [],
            "intentions": [
                {
                    "intention": {
                        "intent": "Request to build a service that can receive text messages and ...",
                        "refs": [
                            "Can you build TextToSummarize which is a SMS number that I can text ..."
                        ]
                    },
                    "sop": {
                        "description": "Intentions related to or including software development, such as ...",
                        "sop": [
                            "Writes a PRD based on software requirements.",
                            "Writes a design to the project repository, based on the PRD of the project.",
                            "Writes a project plan to the project repository, based on the design of the project.",
                            "Writes codes to the project repository, based on the project plan of the project.",
                            "Run QA test on the project repository.",
                            "Stage and commit changes for the project repository using Git."
                        ]
                    }
                },
                {
                    "intention": {
                        "intent": "Request for a phone number to send text messages for the summarization service",
                        "refs": []
                    },
                    "sop": null
                }
            ]
        }
    """
    ctx = Context()
    action = LightIntentDetect(context=ctx)
    await action.run(messages)
    return action.result

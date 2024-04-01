#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import pytest

from metagpt.actions.intent_detect import IntentDetect, LightIntentDetect
from metagpt.logs import logger
from metagpt.schema import Message

DEMO_CONTENT = [
    {
        "role": "user",
        "content": "Can you build TextToSummarize which is a SMS number that I can text and it will scrape a website "
        "and summarize it with ChatGPT",
    },
    {
        "role": "assistant",
        "content": "Absolutely, I can build a service like TextToSummarize for you. The process will involve setting up"
        " an SMS service that can receive your texts, scraping the website content you send, and then using"
        " an AI to summarize the content.\nTo get started, I'll need to set up a number for receiving SMS"
        ", then I'll work on the script to scrape the website content from the URLs you text, and finally."
        " I'll integrate it with an AI service to Generalte the summaries.\n I'll keep you updated on my"
        " progress!",
    },
    {"role": "user", "content": "What exactly do we need the web app for?"},
    {
        "role": "assistant",
        "content": "The web app will service as the interface between the SMS service and the AI summarization service"
        ". When you send a text with a URL to the SMS number, teh web app will process that, scrape the"
        " content from the URL, and then use the AI to summarize it. The summary will then be sent back to"
        " you. It's the central hub that ties all the components of the service togather.",
    },
]

DEMO1_CONTENT = [
    {
        "role": "user",
        "content": "Extract all of the blog posts from `https://stripe.com/blog/page/1` and return a CSV with the"
        " columns `date`, `article_text`, `author` and `summary`. Generate a summary for each article"
        " yourself.",
    }
]

DEMO2_CONTENT = [
    {"role": "user", "content": 'Create a "2048 game"'},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": "TypeError: __init__() takes 1 positional argument but 2 were given"},
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [json.dumps(DEMO1_CONTENT), json.dumps(DEMO_CONTENT), json.dumps(DEMO2_CONTENT)],
)
async def test_intent_detect(content: str, context):
    action = IntentDetect(context=context)
    messages = [Message.model_validate(i) for i in json.loads(content)]
    rsp = await action.run(messages)
    assert isinstance(rsp, Message)
    assert action._dialog_intentions
    assert action._references
    assert action._intent_to_sops
    assert action.result
    logger.info(action.result.model_dump_json())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [json.dumps(DEMO1_CONTENT), json.dumps(DEMO_CONTENT), json.dumps(DEMO2_CONTENT)],
)
async def test_light_intent_detect(content: str, context):
    action = LightIntentDetect(context=context)
    messages = [Message.model_validate(i) for i in json.loads(content)]
    rsp = await action.run(messages)
    assert isinstance(rsp, Message)
    assert action._dialog_intentions
    assert action._intent_to_sops
    assert action.result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

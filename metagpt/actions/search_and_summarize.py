#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 17:26
@Author  : alexanderwu
@File    : search_google.py
"""
from typing import Optional

import pydantic
from pydantic import model_validator

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.tools.search_engine import SearchEngine

SEARCH_AND_SUMMARIZE_SYSTEM = """### Requirements
1. Please summarize the latest dialogue based on the reference information (secondary) and dialogue history (primary). Do not include text that is irrelevant to the conversation.
- The context is for reference only. If it is irrelevant to the user's search request history, please reduce its reference and usage.
2. If there are citable links in the context, annotate them in the main text in the format [main text](citation link). If there are none in the context, do not write links.
3. The reply should be graceful, clear, non-repetitive, smoothly written, and of moderate length, in {LANG}.

### Dialogue History (For example)
A: MLOps competitors

### Current Question (For example)
A: MLOps competitors

### Current Reply (For example)
1. Alteryx Designer: <desc> etc. if any
2. Matlab: ditto
3. IBM SPSS Statistics
4. RapidMiner Studio
5. DataRobot AI Platform
6. Databricks Lakehouse Platform
7. Amazon SageMaker
8. Dataiku
"""

SEARCH_AND_SUMMARIZE_SYSTEM_EN_US = SEARCH_AND_SUMMARIZE_SYSTEM.format(LANG="en-us")

SEARCH_AND_SUMMARIZE_PROMPT = """
### Reference Information
{CONTEXT}

### Dialogue History
{QUERY_HISTORY}
{QUERY}

### Current Question
{QUERY}

### Current Reply: Based on the information, please write the reply to the Question


"""

SEARCH_AND_SUMMARIZE_SALES_SYSTEM = """## Requirements
1. Please summarize the latest dialogue based on the reference information (secondary) and dialogue history (primary). Do not include text that is irrelevant to the conversation.
- The context is for reference only. If it is irrelevant to the user's search request history, please reduce its reference and usage.
2. If there are citable links in the context, annotate them in the main text in the format [main text](citation link). If there are none in the context, do not write links.
3. The reply should be graceful, clear, non-repetitive, smoothly written, and of moderate length, in Simplified Chinese.

# Example
## Reference Information
...

## Dialogue History
user: Which facial cleanser is good for oily skin?
Salesperson: Hello, for oily skin, it is suggested to choose a product that can deeply cleanse, control oil, and is gentle and skin-friendly. According to customer feedback and market reputation, the following facial cleansers are recommended:...
user: Do you have any by L'Oreal?
> Salesperson: ...

## Ideal Answer
Yes, I've selected the following for you:
1. L'Oreal Men's Facial Cleanser: Oil control, anti-acne, balance of water and oil, pore purification, effectively against blackheads, deep exfoliation, refuse oil shine. Dense foam, not tight after washing.
2. L'Oreal Age Perfect Hydrating Cleanser: Added with sodium cocoyl glycinate and Centella Asiatica, two effective ingredients, it can deeply cleanse, tighten the skin, gentle and not tight.
"""

SEARCH_AND_SUMMARIZE_SALES_PROMPT = """
## Reference Information
{CONTEXT}

## Dialogue History
{QUERY_HISTORY}
{QUERY}
> {ROLE}: 

"""

SEARCH_FOOD = """
# User Search Request
What are some delicious foods in Xiamen?

# Requirements
You are a member of a professional butler team and will provide helpful suggestions:
1. Please summarize the user's search request based on the context and avoid including unrelated text.
2. Use [main text](reference link) in markdown format to **naturally annotate** 3-5 textual elements (such as product words or similar text sections) within the main text for easy navigation.
3. The response should be elegant, clear, **without any repetition of text**, smoothly written, and of moderate length.
"""


class SearchAndSummarize(Action):
    name: str = ""
    content: Optional[str] = None
    search_engine: SearchEngine = None
    result: str = ""

    @model_validator(mode="after")
    def validate_search_engine(self):
        if self.search_engine is None:
            try:
                config = self.config
                search_engine = SearchEngine.from_search_config(config.search, proxy=config.proxy)
            except pydantic.ValidationError:
                search_engine = None

            self.search_engine = search_engine
        return self

    async def run(self, context: list[Message], system_text=SEARCH_AND_SUMMARIZE_SYSTEM) -> str:
        if self.search_engine is None:
            logger.warning("Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature")
            return ""

        query = context[-1].content
        # logger.debug(query)
        rsp = await self.search_engine.run(query)
        self.result = rsp
        if not rsp:
            logger.error("empty rsp...")
            return ""
        # logger.info(rsp)

        system_prompt = [system_text]

        prompt = SEARCH_AND_SUMMARIZE_PROMPT.format(
            ROLE=self.prefix,
            CONTEXT=rsp,
            QUERY_HISTORY="\n".join([str(i) for i in context[:-1]]),
            QUERY=str(context[-1]),
        )
        result = await self._aask(prompt, system_prompt)
        logger.debug(prompt)
        logger.debug(result)
        return result

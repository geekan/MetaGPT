#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : alexanderwu
@File    : write_review.py
"""
from typing import List

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode

REVIEW = ActionNode(
    key="Review",
    expected_type=List[str],
    instruction="Act as an experienced Reviewer and review the given output. Ask a series of critical questions, "
    "concisely and clearly, to help the writer improve their work.",
    example=[
        "This is a good PRD, but I think it can be improved by adding more details.",
    ],
)

LGTM = ActionNode(
    key="LGTM",
    expected_type=str,
    instruction="LGTM/LBTM. If the output is good enough, give a LGTM (Looks Good To Me) to the writer, "
    "else LBTM (Looks Bad To Me).",
    example="LGTM",
)

WRITE_REVIEW_NODE = ActionNode.from_children("WRITE_REVIEW_NODE", [REVIEW, LGTM])


class WriteReview(Action):
    """Write a review for the given context."""

    name: str = "WriteReview"

    async def run(self, context):
        return await WRITE_REVIEW_NODE.fill(context=context, llm=self.llm, schema="json")

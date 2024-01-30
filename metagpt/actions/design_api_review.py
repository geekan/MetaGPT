#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:31
@Author  : alexanderwu
@File    : design_api_review.py
"""

from typing import Optional

from metagpt.actions.action import Action


class DesignReview(Action):
    name: str = "DesignReview"
    i_context: Optional[str] = None

    async def run(self, prd, api_design):
        prompt = (
            f"Here is the Product Requirement Document (PRD):\n\n{prd}\n\nHere is the list of APIs designed "
            f"based on this PRD:\n\n{api_design}\n\nPlease review whether this API design meets the requirements"
            f" of the PRD, and whether it complies with good design practices."
        )

        api_review = await self._aask(prompt)
        return api_review

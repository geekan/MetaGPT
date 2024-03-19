#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd_review.py
"""

from typing import Optional

from metagpt.actions.action import Action


class WritePRDReview(Action):
    name: str = ""
    i_context: Optional[str] = None

    prd: Optional[str] = None
    desc: str = "Based on the PRD, conduct a PRD Review, providing clear and detailed feedback"
    prd_review_prompt_template: str = """
Given the following Product Requirement Document (PRD):
{prd}

As a project manager, please review it and provide your feedback and suggestions.
"""

    async def run(self, prd):
        self.prd = prd
        prompt = self.prd_review_prompt_template.format(prd=self.prd)
        review = await self._aask(prompt)
        return review

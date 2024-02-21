#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 17:45
# @Author  : alexanderwu
# @File    : write_prd_review.py


from typing import Optional

from metagpt.actions.action import Action


class WritePRDReview(Action):
    """A class for conducting Product Requirement Document (PRD) reviews.

    This class inherits from the Action class and is designed to provide detailed feedback on PRDs.

    Attributes:
        name: A string representing the name of the action.
        i_context: An optional string providing additional context for the action.
        prd: An optional string representing the PRD to be reviewed.
        desc: A brief description of the action.
        prd_review_prompt_template: A template string used to generate the review prompt.
    """

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
        """Asynchronously runs the PRD review process.

        Args:
            prd: A string representing the Product Requirement Document to be reviewed.

        Returns:
            A string containing the review and feedback for the given PRD.
        """
        self.prd = prd
        prompt = self.prd_review_prompt_template.format(prd=self.prd)
        review = await self._aask(prompt)
        return review

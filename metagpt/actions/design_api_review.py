#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 19:31
# @Author  : alexanderwu
# @File    : design_api_review.py


from typing import Optional

from metagpt.actions.action import Action


class DesignReview(Action):
    """A class for reviewing the design of APIs against product requirements.

    This class inherits from the Action class and is used to review whether the API design meets the requirements of the Product Requirement Document (PRD) and complies with good design practices.

    Attributes:
        name: A string indicating the name of the action.
        i_context: An optional string that provides additional context for the action.
    """

    name: str = "DesignReview"
    i_context: Optional[str] = None

    async def run(self, prd, api_design):
        """Runs the design review process.

        This method takes the product requirement document and the API design as input, and returns a review of the API design based on the requirements and good design practices.

        Args:
            prd: The product requirement document.
            api_design: The API design to be reviewed.

        Returns:
            A string containing the review of the API design.
        """
        prompt = (
            f"Here is the Product Requirement Document (PRD):\n\n{prd}\n\nHere is the list of APIs designed "
            f"based on this PRD:\n\n{api_design}\n\nPlease review whether this API design meets the requirements"
            f" of the PRD, and whether it complies with good design practices."
        )

        api_review = await self._aask(prompt)
        return api_review

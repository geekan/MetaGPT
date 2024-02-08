#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_prd_review.py
"""
import pytest

from metagpt.actions.write_prd_review import WritePRDReview


@pytest.mark.asyncio
async def test_write_prd_review(context):
    prd = """
    Introduction: This is a new feature for our product.
    Goals: The goal is to improve user engagement.
    User Scenarios: The expected user group is millennials who like to use social media.
    Requirements: The feature needs to be interactive and user-friendly.
    Constraints: The feature needs to be implemented within 2 months.
    Mockups: There will be a new button on the homepage that users can click to access the feature.
    Metrics: We will measure the success of the feature by user engagement metrics.
    Timeline: The feature should be ready for testing in 1.5 months.
    """

    write_prd_review = WritePRDReview(name="write_prd_review", context=context)

    prd_review = await write_prd_review.run(prd)

    # We cannot exactly predict the generated PRD review, but we can check if it is a string and if it is not empty
    assert isinstance(prd_review, str)
    assert len(prd_review) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :


from metagpt.context import context


def test_azure_openai_api():
    _ = context.llm("azure")

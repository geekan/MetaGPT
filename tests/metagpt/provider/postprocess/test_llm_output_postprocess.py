#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :


from metagpt.provider.postprocess.llm_output_postprocess import llm_output_postprocess
from tests.metagpt.provider.postprocess.test_base_postprocess_plugin import (
    raw_output,
    raw_schema,
)


def test_llm_output_postprocess():
    output = llm_output_postprocess(output=raw_output, schema=raw_schema)
    assert "Original Requirements" in output

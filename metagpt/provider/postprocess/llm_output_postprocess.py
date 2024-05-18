#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the entry of choosing which PostProcessPlugin to deal particular LLM model's output

from typing import Union

from metagpt.provider.postprocess.base_postprocess_plugin import BasePostProcessPlugin


def llm_output_postprocess(
    output: str, schema: dict, req_key: str = "[/CONTENT]", model_name: str = None
) -> Union[dict, str]:
    """
    default use BasePostProcessPlugin if there is not matched plugin.
    """
    # TODO choose different model's plugin according to the model
    postprocess_plugin = BasePostProcessPlugin()

    result = postprocess_plugin.run(output=output, schema=schema, req_key=req_key)
    return result

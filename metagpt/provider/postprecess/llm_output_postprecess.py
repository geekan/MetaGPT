#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the entry of choosing which PostProcessPlugin to deal particular LLM model's output

from typing import Union

from metagpt.provider.postprecess.base_postprecess_plugin import BasePostPrecessPlugin


def llm_output_postprecess(
    output: str, schema: dict, req_key: str = "[/CONTENT]", model_name: str = None
) -> Union[dict, str]:
    """
    default use BasePostPrecessPlugin if there is not matched plugin.
    """
    # TODO choose different model's plugin according to the model_name
    postprecess_plugin = BasePostPrecessPlugin()

    result = postprecess_plugin.run(output=output, schema=schema, req_key=req_key)
    return result

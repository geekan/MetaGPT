#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :


from metagpt.provider.postprocess.base_postprocess_plugin import BasePostProcessPlugin

raw_output = """
[CONTENT]
{
"Original Requirements": "xxx"
}
[/CONTENT]
"""
raw_schema = {
    "title": "prd",
    "type": "object",
    "properties": {
        "Original Requirements": {"title": "Original Requirements", "type": "string"},
    },
    "required": [
        "Original Requirements",
    ],
}


def test_llm_post_process_plugin():
    post_process_plugin = BasePostProcessPlugin()

    output = post_process_plugin.run(output=raw_output, schema=raw_schema)
    assert "Original Requirements" in output

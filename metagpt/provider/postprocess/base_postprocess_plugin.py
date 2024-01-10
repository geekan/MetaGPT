#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base llm postprocess plugin to do the operations like repair the raw llm output

from typing import Union

from metagpt.utils.repair_llm_raw_output import (
    RepairType,
    extract_content_from_output,
    repair_llm_raw_output,
    retry_parse_json_text,
)


class BasePostProcessPlugin(object):
    model = None  # the plugin of the `model`, use to judge in `llm_postprocess`

    def run_repair_llm_output(self, output: str, schema: dict, req_key: str = "[/CONTENT]") -> Union[dict, list]:
        """
        repair steps
            1. repair the case sensitive problem using the schema's fields
            2. extract the content from the req_key pair( xx[REQ_KEY]xxx[/REQ_KEY]xx )
            3. repair the invalid json text in the content
            4. parse the json text and repair it according to the exception with retry loop
        """
        output_class_fields = list(schema["properties"].keys())  # Custom ActionOutput's fields

        content = self.run_repair_llm_raw_output(output, req_keys=output_class_fields + [req_key])
        content = self.run_extract_content_from_output(content, right_key=req_key)
        # # req_keys mocked
        content = self.run_repair_llm_raw_output(content, req_keys=[None], repair_type=RepairType.JSON)
        parsed_data = self.run_retry_parse_json_text(content)

        return parsed_data

    def run_repair_llm_raw_output(self, content: str, req_keys: list[str], repair_type: str = None) -> str:
        """inherited class can re-implement the function"""
        return repair_llm_raw_output(content, req_keys=req_keys, repair_type=repair_type)

    def run_extract_content_from_output(self, content: str, right_key: str) -> str:
        """inherited class can re-implement the function"""
        return extract_content_from_output(content, right_key=right_key)

    def run_retry_parse_json_text(self, content: str) -> Union[dict, list]:
        """inherited class can re-implement the function"""
        # logger.info(f"extracted json CONTENT from output:\n{content}")
        parsed_data = retry_parse_json_text(output=content)  # should use output=content
        return parsed_data

    def run(self, output: str, schema: dict, req_key: str = "[/CONTENT]") -> Union[dict, list]:
        """
        this is used for prompt with a json-format output requirement and outer pair key, like
            [REQ_KEY]
                {
                    "Key": "value"
                }
            [/REQ_KEY]

        Args
            outer (str): llm raw output
            schema: output json schema
            req_key: outer pair right key, usually in `[/REQ_KEY]` format
        """
        assert len(schema.get("properties")) > 0
        assert "/" in req_key

        # current, postprocess only deal the repair_llm_raw_output
        new_output = self.run_repair_llm_output(output=output, schema=schema, req_key=req_key)
        return new_output

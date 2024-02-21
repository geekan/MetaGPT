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
    """Base class for post-processing plugins.

    This class provides methods to repair and extract content from the output of a language model.

    Attributes:
        model: The model attribute is not defined in this class but can be set in derived classes.
    """

    model = None  # the plugin of the `model`, use to judge in `llm_postprocess`

    def run_repair_llm_output(self, output: str, schema: dict, req_key: str = "[/CONTENT]") -> Union[dict, list]:
        """Repairs the output from a language model according to a given schema and extracts content.

        The repair process includes fixing case sensitivity issues, extracting content based on a key,
        repairing invalid JSON text, and retrying parsing of JSON text with error handling.

        Args:
            output: The raw output from a language model.
            schema: A dictionary representing the schema to which the output should conform.
            req_key: A string representing the key used to extract the relevant content from the output.

        Returns:
            A dictionary or list representing the repaired and extracted content.
        """
        output_class_fields = list(schema["properties"].keys())  # Custom ActionOutput's fields

        content = self.run_repair_llm_raw_output(output, req_keys=output_class_fields + [req_key])
        content = self.run_extract_content_from_output(content, right_key=req_key)
        # # req_keys mocked
        content = self.run_repair_llm_raw_output(content, req_keys=[None], repair_type=RepairType.JSON)
        parsed_data = self.run_retry_parse_json_text(content)

        return parsed_data

    def run_repair_llm_raw_output(self, content: str, req_keys: list[str], repair_type: str = None) -> str:
        """Placeholder for inherited class implementation to repair raw output content.

        Args:
            content: The content to be repaired.
            req_keys: A list of keys required for the repair process.
            repair_type: The type of repair to be performed.

        Returns:
            The repaired content as a string.
        """
        return repair_llm_raw_output(content, req_keys=req_keys, repair_type=repair_type)

    def run_extract_content_from_output(self, content: str, right_key: str) -> str:
        """Placeholder for inherited class implementation to extract content from output.

        Args:
            content: The content from which to extract.
            right_key: The key indicating the end of the content to be extracted.

        Returns:
            The extracted content as a string.
        """
        return extract_content_from_output(content, right_key=right_key)

    def run_retry_parse_json_text(self, content: str) -> Union[dict, list]:
        """Placeholder for inherited class implementation to parse JSON text with retries.

        Args:
            content: The JSON content to be parsed.

        Returns:
            The parsed content as a dictionary or list.
        """
        # logger.info(f"extracted json CONTENT from output:\n{content}")
        parsed_data = retry_parse_json_text(output=content)  # should use output=content
        return parsed_data

    def run(self, output: str, schema: dict, req_key: str = "[/CONTENT]") -> Union[dict, list]:
        """Processes the output from a language model and returns structured data.

        This method is intended for use with outputs that are expected to be in JSON format,
        enclosed within specified keys.

        Args:
            output: The raw output from a language model.
            schema: A dictionary representing the expected JSON schema of the output.
            req_key: A string representing the key used to enclose the JSON content in the output.

        Returns:
            A dictionary or list representing the structured data extracted and repaired from the output.
        """
        assert len(schema.get("properties")) > 0
        assert "/" in req_key

        # current, postprocess only deal the repair_llm_raw_output
        new_output = self.run_repair_llm_output(output=output, schema=schema, req_key=req_key)
        return new_output

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : human interaction to get required type text

import json
from typing import Any, Tuple, Type

from pydantic import BaseModel

from metagpt.logs import logger
from metagpt.utils.common import import_class


class HumanInteraction(object):
    """A class to handle human interactions through the console.

    This class provides methods to input multi-line text, check the type of the input,
    and interact with structured content based on user input.

    Attributes:
        stop_list: A tuple containing strings that signal the end of an interaction.
    """

    stop_list = ("q", "quit", "exit")

    def multilines_input(self, prompt: str = "Enter: ") -> str:
        """Takes multi-line input from the user until an EOF signal is received.

        Args:
            prompt: A string to display before waiting for input.

        Returns:
            A string containing all the lines of input concatenated together.
        """
        logger.warning("Enter your content, use Ctrl-D or Ctrl-Z ( windows ) to save it.")
        logger.info(f"{prompt}\n")
        lines = []
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break
        return "".join(lines)

    def check_input_type(self, input_str: str, req_type: Type) -> Tuple[bool, Any]:
        """Checks if the input string can be converted to a specified type.

        Args:
            input_str: The input string to check.
            req_type: The required type to which the input should be converted.

        Returns:
            A tuple containing a boolean indicating success or failure, and the converted input or None.
        """
        check_ret = True
        if req_type == str:
            # required_type = str, just return True
            return check_ret, input_str
        try:
            input_str = input_str.strip()
            data = json.loads(input_str)
        except Exception:
            return False, None

        actionnode_class = import_class("ActionNode", "metagpt.actions.action_node")  # avoid circular import
        tmp_key = "tmp"
        tmp_cls = actionnode_class.create_model_class(class_name=tmp_key.upper(), mapping={tmp_key: (req_type, ...)})
        try:
            _ = tmp_cls(**{tmp_key: data})
        except Exception:
            check_ret = False
        return check_ret, data

    def input_until_valid(self, prompt: str, req_type: Type) -> Any:
        """Repeatedly prompts the user for input until it can be converted to the required type.

        Args:
            prompt: A string to display before waiting for input.
            req_type: The required type to which the input should be converted.

        Returns:
            The user input converted to the required type.
        """
        # check the input with req_type until it's ok
        while True:
            input_content = self.multilines_input(prompt)
            check_ret, structure_content = self.check_input_type(input_content, req_type)
            if check_ret:
                break
            else:
                logger.error(f"Input content can't meet required_type: {req_type}, please Re-Enter.")
        return structure_content

    def input_num_until_valid(self, num_max: int) -> int:
        """Prompts the user for a number until a valid number is entered or a stop signal is received.

        Args:
            num_max: The maximum valid number (exclusive).

        Returns:
            The valid number entered by the user, or a stop signal string.
        """
        while True:
            input_num = input("Enter the num of the interaction key: ")
            input_num = input_num.strip()
            if input_num in self.stop_list:
                return input_num
            try:
                input_num = int(input_num)
                if 0 <= input_num < num_max:
                    return input_num
            except Exception:
                pass

    def interact_with_instruct_content(
        self, instruct_content: BaseModel, mapping: dict = dict(), interact_type: str = "review"
    ) -> dict[str, Any]:
        """Facilitates interaction with structured content based on user input.

        Args:
            instruct_content: A Pydantic BaseModel instance containing the structured content.
            mapping: A dictionary mapping field names to their required types.
            interact_type: The type of interaction, either 'review' or 'revise'.

        Returns:
            A dictionary containing the fields interacted with and their new content.
        """
        assert interact_type in ["review", "revise"]
        assert instruct_content
        instruct_content_dict = instruct_content.model_dump()
        num_fields_map = dict(zip(range(0, len(instruct_content_dict)), instruct_content_dict.keys()))
        logger.info(
            f"\n{interact_type.upper()} interaction\n"
            f"Interaction data: {num_fields_map}\n"
            f"Enter the num to interact with corresponding field or `q`/`quit`/`exit` to stop interaction.\n"
            f"Enter the field content until it meet field required type.\n"
        )

        interact_contents = {}
        while True:
            input_num = self.input_num_until_valid(len(instruct_content_dict))
            if input_num in self.stop_list:
                logger.warning("Stop human interaction")
                break

            field = num_fields_map.get(input_num)
            logger.info(f"You choose to interact with field: {field}, and do a `{interact_type}` operation.")

            if interact_type == "review":
                prompt = "Enter your review comment: "
                req_type = str
            else:
                prompt = "Enter your revise content: "
                req_type = mapping.get(field)[0]  # revise need input content match the required_type

            field_content = self.input_until_valid(prompt=prompt, req_type=req_type)
            interact_contents[field] = field_content

        return interact_contents

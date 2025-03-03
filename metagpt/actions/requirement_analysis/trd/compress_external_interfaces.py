#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : compress_external_interfaces.py
@Desc    : The implementation of Chapter 2.1.5 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import general_after_log


@register_tool(include_functions=["run"])
class CompressExternalInterfaces(Action):
    """CompressExternalInterfaces deal with the following situations:
    1. Given a natural text of acknowledgement, it extracts and compresses the information about external system interfaces.
    """

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def run(
        self,
        *,
        acknowledge: str,
    ) -> str:
        """
        Extracts and compresses information about external system interfaces from a given acknowledgement text.

        Args:
            acknowledge (str): A natural text of acknowledgement containing details about external system interfaces.

        Returns:
            str: A compressed version of the information about external system interfaces.

        Example:
            >>> compress_acknowledge = CompressExternalInterfaces()
            >>> acknowledge = "## Interfaces\\n..."
            >>> available_external_interfaces = await compress_acknowledge.run(acknowledge=acknowledge)
            >>> print(available_external_interfaces)
            ```json\n[\n{\n"id": 1,\n"inputs": {...
        """
        return await self.llm.aask(
            msg=acknowledge,
            system_msgs=[
                "Extracts and compresses the information about external system interfaces.",
                "Return a markdown JSON list of objects, each object containing:\n"
                '- an "id" key containing the interface id;\n'
                '- an "inputs" key containing a dict of input parameters that consist of name and description pairs;\n'
                '- an "outputs" key containing a dict of returns that consist of name and description pairs;\n',
            ],
        )

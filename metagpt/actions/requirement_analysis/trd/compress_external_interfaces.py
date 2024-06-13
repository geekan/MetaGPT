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
from metagpt.utils.common import general_after_log


class CompressExternalInterfaces(Action):
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
        return await self.llm.aask(
            msg=acknowledge,
            system_msgs=[
                "Return a markdown JSON list of objects, each object containing:\n"
                '- an "id" key containing the interface id;\n'
                '- an "inputs" key containing a dict of input parameters that consist of name and description pairs;\n'
                '- an "outputs" key containing a dict of returns that consist of name and description pairs;\n'
            ],
        )

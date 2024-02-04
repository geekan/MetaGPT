# -*- coding: utf-8 -*-
# @Date    : 1/11/2024 7:06 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main(requirement: str = ""):
    code_interpreter = CodeInterpreter(use_tools=True, goal=requirement)
    await code_interpreter.run(requirement)


if __name__ == "__main__":
    sd_url = "http://your.sd.service.ip:port"
    requirement = (
        f"I want to generate an image of a beautiful girl using the stable diffusion text2image tool, sd_url={sd_url}"
    )

    asyncio.run(main(requirement))

# -*- coding: utf-8 -*-
# @Date    : 1/11/2024 7:06 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(requirement: str = ""):
    di = DataInterpreter(tools=["SDEngine"])
    await di.run(requirement)


if __name__ == "__main__":
    sd_url = "http://your.sd.service.ip:port"
    requirement = (
        f"I want to generate an image of a beautiful girl using the stable diffusion text2image tool, sd_url={sd_url}"
    )

    asyncio.run(main(requirement))

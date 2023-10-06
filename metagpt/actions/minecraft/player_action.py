# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 17:06
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.actions import Action

class PlayerActions(Action):
    """Minecraft player info without any implementation details"""
    async def run(self, *args, **kwargs):
        raise NotImplementedError
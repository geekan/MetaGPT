# -*- coding: utf-8 -*-
# @Date    : 2023/9/24 11:09
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio

from metagpt.roles.minecraft.curriculum_agent import CurriculumDesigner
from metagpt.roles.minecraft.skill_manager import SkillManager
from metagpt.roles.minecraft.action_developer import ActionDeveloper
from metagpt.roles.minecraft.critic_agent import CriticReviewer
from metagpt.minecraft_team import MinecraftPlayer


async def learn(task="Start", investment: float = 50.0, n_round: int = 3):
    mc_player = MinecraftPlayer()
    mc_player.set_port(33141) # Modify this to your Minecraft LAN port
    # mc_player.set_resume(True) # If load json from ckpt dir(include chest_memory, skills, ...)
    mc_player.hire(
        [
            CurriculumDesigner(),
            ActionDeveloper(),
            CriticReviewer(),
            SkillManager(),
        
        ]
    )
    print(mc_player.environment.roles)
    print(mc_player.environment.roles["Generate code for specified tasks"]._rc) 
    mc_player.invest(investment)
    mc_player.start(task)
    await mc_player.run(n_round=n_round)


if __name__ == "__main__":
    asyncio.run(learn())

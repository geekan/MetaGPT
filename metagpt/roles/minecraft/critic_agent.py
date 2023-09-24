# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:46
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.actions.minecraft.review_task import VerifyTask
from metagpt.actions.minecraft.generate_actions import GenerateActionCode

class CriticReviewer(Base):
    """
    self-verification
    """
    def __init__(
            self,
            name: str = "Simon",
            profile: str = "Task Reviewer",
            goal: str = "To provide insightful and constructive feedback on a wide range of content types, helping creators improve their work and maintaining high-quality standards.",
            constraints: str = "Adherence to ethical reviewing practices, respectful communication, and confidentiality of sensitive information.",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the CriticReviewer role
        self._init_actions([VerifyTask])
        
        # Set events or actions the CriticReviewer should watch or be aware of
        # 需要获取最新的events来进行评估
        self._watch([GenerateActionCode])
    
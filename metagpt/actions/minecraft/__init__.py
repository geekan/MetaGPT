# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:26
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from enum import Enum

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.minecraft.design_curriculumn import DesignTask, DesignCurriculum
from metagpt.actions.minecraft.generate_actions import GenerateActionCode, SummarizeLog
from metagpt.actions.minecraft.manage_skills import RetrieveSkills, GenerateSkillDescription, AddNewSkills
from metagpt.actions.minecraft.review_task import VerifyTask
from metagpt.actions.minecraft.player_action import PlayerActions


class ActionType(Enum):
    """All types of Actions, used for indexing."""

    Design_Task = DesignTask
    Design_Curriculum = DesignCurriculum
    Generate_Action_Code = GenerateActionCode
    Summarize_Log = SummarizeLog
    Retrieve_Skills = RetrieveSkills
    Generate_Skill_Description = GenerateSkillDescription
    Add_New_Skills = AddNewSkills
    Verify_Task = VerifyTask
    Player_Actions = PlayerActions



__all__ = [
    "ActionType",
    "Action",
    "ActionOutput",
]

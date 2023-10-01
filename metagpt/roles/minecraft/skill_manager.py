# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:46
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.roles.minecraft.minecraft_base import agent_registry
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.actions.minecraft.manage_skills import GenerateSkillDescription, RetrieveSkills, AddNewSkills
from metagpt.actions.minecraft.review_task import VerifyTask
from metagpt.actions.minecraft.design_curriculumn import DesignCurriculum



@agent_registry.register("skill_manager")
class SkillManager(Base):
    def __init__(
            self,
            name: str = "John",
            profile: str = "Skills Management Specialist",
            goal: str = "To oversee and optimize the acquisition, development, and utilization of skills within the organization, ensuring workforce competence and efficiency.",
            constraints: str = "Resource allocation, training budgets, and alignment with organizational goals.",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the SkillManager role
        self._init_actions([RetrieveSkills, GenerateSkillDescription]) #AddNewSkills])#先去掉add
        
        # Set events or actions the SkillManager should watch or be aware of
        self._watch([DesignCurriculum, VerifyTask, RetrieveSkills, GenerateSkillDescription])
    
    async def retrieve_skills(self, human_msg, system_msg, *args, **kwargs):
        skills = await RetrieveSkills().run(human_msg)
        logger.info(
            f"\033[33mRender Action Agent system message with {len(skills)} skills\033[0m"
        )
        return Message(content=f"{skills}", instruct_content="retrieve_skills", role=self.profile,
                       send_to=agent_registry.entries["action_developer"]()._setting.name)
    
    async def generate_skill_descp(self, human_msg, system_msg, *args, **kwargs):
        desp = await GenerateSkillDescription().run(human_msg)
        return Message(content=f"{desp}", instruct_content="generate_skill_descp", role=self.profile)
    
    async def handle_add_new_skills(self, human_msg, system_msg, *args, **kwargs):
        new_skills = await AddNewSkills().run(human_msg)
        return Message(content=f"", instruct_content="generate_skill_descp", role=self.profile)
    
    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        self.maintain_actions(todo)    
        # 获取最新的游戏周边信息
        context = self.game_memory.context
        
        msg = self._rc.memory.get(k=1)[0]
        
        message = self.encapsule_message(context)
        
        handler_map = {
            DesignCurriculum: self.retrieve_skills,
            RetrieveSkills: self.retrieve_skills,
            GenerateSkillDescription: self.generate_skill_descp,
            AddNewSkills: self.handle_add_new_skills,
        }
        handler = handler_map.get(type(todo))
        if handler:
            msg = await handler(**message)
            msg.cause_by = type(todo)
            msg.round_id = self.round_id
            self._publish_message(msg)
            return msg
        
        raise ValueError(f"Unknown todo type: {type(todo)}")

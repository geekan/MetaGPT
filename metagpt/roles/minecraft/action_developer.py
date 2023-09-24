# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:45
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.roles.minecraft.minecraft_base import agent_registry
from metagpt.actions.minecraft.generate_actions import GenerateActionCode
from metagpt.actions.minecraft.design_curriculumn import DesignCurriculum
from metagpt.actions.minecraft.manage_skills import GenerateSkillDescription, RetrieveSkills, AddNewSkills


@agent_registry.register("action_developer")
class ActionDeveloper(Base):
    """
    iterative prompting mechanism in paper.
    generate action code based on environment observation and plan, as well as skills retrieval results
    """
    
    def __init__(
            self,
            name: str = "Bob",
            profile: str = "Generate code for specified tasks",
            goal: str = "Produce accurate and efficient code solutions in Python and JavaScript",
            constraints: str = "Adhere to coding best practices and style guidelines",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the Action role
        self._init_actions([GenerateActionCode])
        
        # Set events or actions the ActionAgent should watch or be aware of
        # 需要根据events进行自己chest_observation的更新
        self._watch([RetrieveSkills])
    
    async def _observe(self) -> int:
        await super()._observe()
        for msg in self._rc.news:
            logger.info(msg.send_to == self._setting.name)
        self._rc.news = [
            msg for msg in self._rc.news if msg.send_to == self._setting.name
        ]  # only relevant msgs count as observed news
        logger.info(len(self._rc.news))
        return len(self._rc.news)
    
    async def generate_action_code(self, human_msg, system_msg, *args, **kwargs):
        code = await GenerateActionCode().run(human_msg)
        logger.info(code)
        msg = Message(content=f"test_action", instruct_content="generate_action_code", role=self.profile)
        logger.info(msg)
        return msg
        
    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        
        # 获取最新的游戏周边信息
        context = self.game_memory.context
        task = self.game_memory.current_task

        message = self.encapsule_message(task, context)
        logger.info(todo)
        handler_map = {

            GenerateActionCode: self.generate_action_code,
        }
        handler = handler_map.get(type(todo))
        logger.info(handler)

        if handler:
            msg = await handler(**message)
            logger.info(msg)
            msg.cause_by = type(todo)
            logger.info(msg.send_to)
            self._publish_message(msg)
            return msg
        
        raise ValueError(f"Unknown todo type: {type(todo)}")
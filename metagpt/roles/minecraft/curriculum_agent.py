# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:45
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.actions.minecraft.design_curriculumn import DesignCurriculum, DesignTask
from metagpt.actions.minecraft.player_action import PlayerActions


class CurriculumDesigner(Base):
    """
    CurriculumDesigner is the automatic curriculum in paper, refer to the code voyager/agents/curriculum.py
    """
    
    def __init__(
            self,
            name: str = "David",
            profile: str = "Expertise in minecraft task design and curriculum development.",
            goal: str = " Collect and integrate learner feedback to improve and refine educational content and pathways",
            constraints: str = "Limited budget and resources for the development of educational content and technology tools."
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the Action role
        self._init_actions([DesignTask, DesignCurriculum])
        
        # Set events or actions the ActionAgent should watch or be aware of
        self._watch([PlayerActions, DesignTask])
    
    def render_human_message(self, msg, *args, **kwargs):
        return HumanMessage(content=msg)
    
    def render_system_message(self, msg, *args, **kwargs):
        return SystemMessage(content=msg)
    
    async def handle_task_design(self, human_msg, system_msg, *args, **kwargs):
        """
        Args:
            human_msg:
            system_msg:
            *args:
            **kwargs:

        Returns:
        """
        task = await DesignTask().run(human_msg, system_msg, *args, **kwargs)
        self.perform_game_info_callback(task, self.game_memory.update_task)
        return Message(content=f"{task}", instruct_content="task_design", role=self.profile)
    
    async def handle_curriculum_design(self, human_msg, system_msg, *args, **kwargs):
        """
        refer to the context generation in voyager
        Args:
            human_msg:
            system_msg:
            *args:
            **kwargs:

        Returns:

        """
        context = await DesignCurriculum().run(human_msg, system_msg, *args, **kwargs)
        self.perform_game_info_callback(context, self.game_memory.update_context)
        return Message(content=f"{context}", instruct_content="curriculum_design", role=self.profile)
    
    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        
        # 获取最新的游戏周边环境信息
        event = await self._obtain_events()
        task = self.game_memory.current_task
        context = self.game_memory.context
        
        msg = self._rc.memory.get(k=1)[0]
        query = msg.content
        
        message = self.encapsule_message(query, task, event)
        
        handler_map = {
            
            DesignTask: self.handle_task_design,
            DesignCurriculum: self.handle_curriculum_design,
        }
        handler = handler_map.get(type(todo))
        if handler:
            msg = await handler(**message)
            msg.cause_by = type(todo)
            self._publish_message(msg)
            return msg
        
        raise ValueError(f"Unknown todo type: {type(todo)}")

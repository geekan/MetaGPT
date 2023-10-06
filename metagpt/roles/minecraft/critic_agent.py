# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:46
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.actions.minecraft.generate_actions import GenerateActionCode
from metagpt.actions.minecraft.manage_skills import AddNewSkills

from metagpt.roles.minecraft.minecraft_base import agent_registry
from metagpt.actions.minecraft.review_task import VerifyTask
from metagpt.utils.minecraft import load_prompt
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.logs import logger


@agent_registry.register("critic_agent")
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
        # self._init_actions([VerifyTask])
        self._init_actions([VerifyTask])

        # Set events or actions the CriticReviewer should watch or be aware of
        # 需要获取最新的events来进行评估
        self._watch([])

    async def run(self, message=None):
        """Observe, only get the observation"""
        if message:
            if isinstance(message, str):
                message = Message(message)
            if isinstance(message, Message):
                self.recv(message)
            if isinstance(message, list):
                self.recv(Message("\n".join(message)))
        elif not await self._observe():
            # If there is no new information, suspend and wait
            logger.info(f"{self._setting}: no news. waiting.")
            return
        self._rc.todo = VerifyTask

    def render_system_message(self):
        system_message = SystemMessage(content=load_prompt("critic"))
        return system_message

    def render_human_message(self, events, task, context, chest_observation):
        assert events[-1][0] == "observe", "Last event must be observe"
        biome = events[-1][1]["status"]["biome"]
        time_of_day = events[-1][1]["status"]["timeOfDay"]
        voxels = events[-1][1]["voxels"]
        health = events[-1][1]["status"]["health"]
        hunger = events[-1][1]["status"]["food"]
        position = events[-1][1]["status"]["position"]
        equipment = events[-1][1]["status"]["equipment"]
        inventory_used = events[-1][1]["status"]["inventoryUsed"]
        inventory = events[-1][1]["inventory"]

        for i, (event_type, event) in enumerate(events):
            if event_type == "onError":
                logger.info(
                    f"\033[31mCritic Agent: Error occurs {event['onError']}\033[0m"
                )
                # return None
                return HumanMessage(content="")

        observation = ""

        observation += f"Biome: {biome}\n\n"

        observation += f"Time: {time_of_day}\n\n"

        if voxels:
            observation += f"Nearby blocks: {', '.join(voxels)}\n\n"
        else:
            observation += f"Nearby blocks: None\n\n"

        observation += f"Health: {health:.1f}/20\n\n"
        observation += f"Hunger: {hunger:.1f}/20\n\n"

        observation += f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n"

        observation += f"Equipment: {equipment}\n\n"

        if inventory:
            observation += f"Inventory ({inventory_used}/36): {inventory}\n\n"
        else:
            observation += f"Inventory ({inventory_used}/36): Empty\n\n"

        observation += chest_observation

        observation += f"Task: {task}\n\n"

        if context:
            observation += f"Context: {context}\n\n"
        else:
            observation += f"Context: None\n\n"
        logger.info(f"****Critic Agent human message****\n: {observation}")
        return HumanMessage(content=observation)

    def encapsule_message(
        self,
        events,
        task,
        context,
        chest_observation,
        *args,
        **kwargs,
    ):
        system_message = self.render_system_message()
        human_message = self.render_human_message(
            events=events,
            task=task,
            context=context,
            chest_observation=chest_observation,
        )

        return {
            "system_msg": [system_message.content],
            "human_msg": human_message.content,
        }

    async def verify_task(self, human_msg, system_msg, *args, **kwargs):
        success, critique = await VerifyTask().run(human_msg, system_msg, max_retries=5)
        self.perform_game_info_callback(
            success, self.game_memory.update_exploration_progress
        )
        self.perform_game_info_callback(critique, self.game_memory.update_critique)
        return Message(
            content=f"{critique}",
            instruct_content="verify_task",
            role=self.profile,
            send_to=agent_registry.entries["skill_manager"]()._setting.name,
        )  # addnewskill
        # TODO:if not success

    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        self.maintain_actions(todo)
        # 获取最新的游戏周边信息
        events = await self._obtain_events()
        self.perform_game_info_callback(
            events, self.game_memory.update_event
        )  # update chest_memory / chest observation
        context = self.game_memory.context
        task = self.game_memory.current_task
        chest_observation = self.game_memory.chest_observation

        message = self.encapsule_message(
            events=events,
            task=task,
            context=context,
            chest_observation=chest_observation,
        )
        logger.info(todo)
        handler_map = {
            VerifyTask: self.verify_task,
        }
        handler = handler_map.get(type(todo))
        logger.info(handler)
        if handler:
            msg = await handler(**message)
            msg.cause_by = type(todo)
            msg.round_id = self.round_id
            logger.info(msg.send_to)
            self._publish_message(msg)
            return msg

        raise ValueError(f"Unknown todo type: {type(todo)}")

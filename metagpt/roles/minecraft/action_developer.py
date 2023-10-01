# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:45
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.roles.minecraft.minecraft_base import agent_registry
from metagpt.actions.minecraft.generate_actions import GenerateActionCode
from metagpt.actions.minecraft.manage_skills import (
    GenerateSkillDescription,
    RetrieveSkills,
    AddNewSkills,
)
import metagpt.utils.minecraft as utils
from metagpt.config import CONFIG
from metagpt.actions.minecraft.control_primitives_context import (
    load_skills_code_context,
)


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

    def render_system_message(self, skills=[], *args, **kwargs):
        """
        According to basic skills context files to genenarate js skill codes.
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/action.py
        """

        action_template = utils.load_prompt("action_template")
        base_skills = [
            "exploreUntil",
            "mineBlock",
            "craftItem",
            "placeItem",
            "smeltItem",
            "killMob",
        ]
        if not CONFIG.openai_api_model == "gpt-3.5-turbo":
            base_skills += [
                "useChest",
                "mineflayer",
            ]
        programs = "\n\n".join(load_skills_code_context(base_skills) + skills)
        response_format = utils.load_prompt("action_response_format")
        system_action_prompt = action_template.format(
            programs=programs, response_format=response_format
        )
        system_action_message = SystemMessage(content=system_action_prompt)
        assert isinstance(system_action_message, SystemMessage)
        return system_action_message

    def render_human_message(
        self, events, code="", task="", context="", critique="", *args, **kwargs
    ):
        """
        Integrate observation about the environment(especially events), add to HumanMessage.
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/action.py
        """

        # Deal with events info
        chat_messages = []
        error_messages = []
        # damage_messages = [] # TODO: try to add damage_messages into prompt later
        assert events[-1][0] == "observe", "Last event must be observe"

        for i, (event_type, event) in enumerate(events):
            if event_type == "onChat":
                chat_messages.append(event["onChat"])
            elif event_type == "onError":
                error_messages.append(event["onError"])
            elif event_type == "observe":
                biome = event["status"]["biome"]
                time_of_day = event["status"]["timeOfDay"]
                voxels = event["voxels"]
                entities = event["status"]["entities"]
                health = event["status"]["health"]
                hunger = event["status"]["food"]
                position = event["status"]["position"]
                equipment = event["status"]["equipment"]
                inventory_used = event["status"]["inventoryUsed"]
                inventory = event["inventory"]
                assert i == len(events) - 1, "observe must be the last event"

        # Collect all the environment information into a str: observation
        observation = ""

        observation = (
            f"Code from the last round:\n{code or 'No code in the first round'}\n\n"
        )

        if error_messages:
            error = "\n".join(error_messages)
            observation += f"Execution error:\n{error}\n\n"
        else:
            observation += f"Execution error: No error\n\n"

        if chat_messages:
            chat_log = "\n".join(chat_messages)
            observation += f"Chat log: {chat_log}\n\n"
        else:
            observation += f"Chat log: None\n\n"

        observation += f"Biome: {biome}\n\n"
        observation += f"Time: {time_of_day}\n\n"
        observation += f"Nearby blocks: {', '.join(voxels) if voxels else 'None'}\n\n"

        if entities:
            nearby_entities = [
                k for k, v in sorted(entities.items(), key=lambda x: x[1])
            ]
            observation += f"Nearby entities (nearest to farthest): {', '.join(nearby_entities)}\n\n"
        else:
            observation += f"Nearby entities (nearest to farthest): None\n\n"

        observation += f"Health: {health:.1f}/20\n\n"
        observation += f"Hunger: {hunger:.1f}/20\n\n"
        observation += f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n"
        observation += f"Equipment: {equipment}\n\n"
        observation += f"Inventory ({inventory_used}/36): {'Empty' if not inventory else ', '.join(inventory)}\n\n"

        if not (
            task == "Place and deposit useless items into a chest"
            or task.startswith("Deposit useless items into the chest at")
        ):
            observation += self.game_memory.chest_observation

        observation += f"Task: {task}\n\n"
        observation += f"Context: {context or 'None'}\n\n"
        observation += f"Critique: {critique or 'None'}\n\n"

        return HumanMessage(content=observation)

    def encapsule_message(
        self,
        events,
        code="",
        task="",
        context="",
        critique="",
        skills=[],
        *args,
        **kwargs,
    ):
        system_message = self.render_system_message(skills=skills)
        human_message = self.render_human_message(
            events=events, code=code, task=task, context=context, critique=critique
        )
        return {
            "system_msg": [system_message.content],
            "human_msg": human_message.content,
        }

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
        code = await GenerateActionCode().run(human_msg, system_msg, *args, **kwargs)
        # logger.warning(type(code))
        # logger.info(f"Code is Here:{code}")
        self.perform_game_info_callback(code, self.game_memory.update_code)
        msg = Message(
            content=f"{code}",
            instruct_content="generate_action_code",
            role=self.profile,
        )
        # logger.info(msg)
        return msg

    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        self.maintain_actions(todo)
        # 获取最新的游戏周边信息
        events = await self._obtain_events()
        self.perform_game_info_callback(events, self.game_memory.update_event)
        context = self.game_memory.context
        task = self.game_memory.current_task
        code = self.game_memory.code
        critique = self.game_memory.critique
        skills = self.game_memory.skills

        message = self.encapsule_message(
            events=events,
            code=code,
            task=task,
            context=context,
            critique=critique,
            skills=skills,
        )
        logger.info(todo)
        handler_map = {
            GenerateActionCode: self.generate_action_code,
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

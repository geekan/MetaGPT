# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 12:45
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import random
import json

from metagpt.logs import logger
from metagpt.schema import Message, HumanMessage, SystemMessage
from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.actions.minecraft.design_curriculumn import DesignCurriculum, DesignTask
from metagpt.actions.minecraft.player_action import PlayerActions
from metagpt.utils.minecraft import load_prompt
from metagpt.const import CKPT_DIR, CURRICULUM_OB


class CurriculumDesigner(Base):
    """
    CurriculumDesigner is the automatic curriculum in paper, refer to the code voyager/agents/curriculum.py
    """
    
    def __init__(
            self,
            name: str = "David",
            profile: str = "Expertise in minecraft task design and curriculum development.",
            goal: str = " Collect and integrate learner feedback to improve and refine educational content and pathways",
            constraints: str = "Limited budget and resources for the development of educational content and technology tools.",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the Action role
        self._init_actions([DesignTask, DesignCurriculum])
        
        # Set events or actions the ActionAgent should watch or be aware of
        self._watch([PlayerActions, DesignTask])
        logger.info(self._actions)
        self.finish_state = len(self._actions)
    
    def render_curriculum_observation(self, *, events, chest_observation):
        """
        Returns: observation for curriculum
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/curriculum.py
        """
        
        assert events[-1][0] == "observe", "Last event must be observe"
        event = events[-1][1]
        biome = event["status"]["biome"]
        time_of_day = event["status"]["timeOfDay"]
        voxels = event["voxels"]
        block_records = event["blockRecords"]
        entities = event["status"]["entities"]
        health = event["status"]["health"]
        hunger = event["status"]["food"]
        position = event["status"]["position"]
        equipment = event["status"]["equipment"]
        inventory_used = event["status"]["inventoryUsed"]
        inventory = event["inventory"]
        
        if not any(
                "dirt" in block
                or "log" in block
                or "grass" in block
                or "sand" in block
                or "snow" in block
                for block in voxels
        ):
            biome = "underground"
        
        other_blocks = ", ".join(
            list(
                set(block_records).difference(set(voxels).union(set(inventory.keys())))
            )
        )
        
        other_blocks = other_blocks if other_blocks else "None"
        
        nearby_entities = (
            ", ".join([k for k, v in sorted(entities.items(), key=lambda x: x[1])])
            if entities
            else "None"
        )
        
        completed_tasks = (
            ", ".join(self.game_memory.completed_tasks)
            if self.game_memory.completed_tasks
            else "None"
        )
        failed_tasks = (
            ", ".join(self.game_memory.failed_tasks)
            if self.game_memory.failed_tasks
            else "None"
        )
        
        # filter out optional inventory items if required
        if (
                self.game_memory.progress
                < self.game_memory.warm_up["optional_inventory_items"]
        ):
            inventory = {
                k: v
                for k, v in inventory.items()
                if self.game_memory.core_inv_items_regex.search(k) is not None
            }
        
        observation = {
            "context": "",
            "biome": f"Biome: {biome}\n\n",
            "time": f"Time: {time_of_day}\n\n",
            "nearby_blocks": f"Nearby blocks: {', '.join(voxels) if voxels else 'None'}\n\n",
            "other_blocks": f"Other blocks that are recently seen: {other_blocks}\n\n",
            "nearby_entities": f"Nearby entities: {nearby_entities}\n\n",
            "health": f"Health: {health:.1f}/20\n\n",
            "hunger": f"Hunger: {hunger:.1f}/20\n\n",
            "position": f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n",
            "equipment": f"Equipment: {equipment}\n\n",
            "inventory": f"Inventory ({inventory_used}/36): {inventory if inventory else 'Empty'}\n\n",
            "chests": chest_observation,
            "completed_tasks": f"Completed tasks so far: {completed_tasks}\n\n",
            "failed_tasks": f"Failed tasks that are too hard: {failed_tasks}\n\n",
        }
        return observation
    
    # --------------------------------Design Task Prepare---------------------------------------
    async def render_design_task_human_message(
            self, events, chest_observation, *args, **kwargs
    ):
        """
        Returns: observation for curriculum
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/curriculum.py
        """
        
        content = ""
        warm_up = self.game_memory.mf_instance.warm_up
        observation = self.render_curriculum_observation(
            events=events, chest_observation=chest_observation
        )
        if self.game_memory.progress >= warm_up["context"]:
            # if self.game_memory.progress >= 0: # TEST ONLY
            human_msg = self.render_design_curriculum_human_message(
                events=events, chest_observation=chest_observation
            ).content
            system_msg = [self.render_design_curriculum_system_message().content]
            questions, answers = await self.curriculum_design_action.generate_qa(
                events=events, human_msg=human_msg, system_msg=system_msg
            )
            logger.debug(f"Generate_qa result is HERE: Ques: {questions}, Ans: {answers}")
            i = 1
            for question, answer in zip(questions, answers):
                if "Answer: Unknown" in answer or "language model" in answer:
                    continue
                observation["context"] += f"Question {i}: {question}\n"
                observation["context"] += f"{answer}\n\n"
                i += 1
                if i > 5:
                    break
        
        for key in CURRICULUM_OB:
            if self.game_memory.progress >= warm_up[key]:
                if warm_up[key] != 0:
                    should_include = random.random() < 0.8
                else:
                    should_include = True
                if should_include:
                    content += observation[key]
        
        logger.info(f"Curriculum Agent human message\n{content}")
        return HumanMessage(content=content)
    
    def render_design_task_system_message(self, *args, **kwargs):
        return SystemMessage(content=load_prompt("curriculum"))
    
    async def encapsule_design_task_message(self, events, chest_observation, *args, **kwargs):
        human_msg = await self.render_design_task_human_message(
            events=events, chest_observation=chest_observation, *args, **kwargs
        )
        system_msg = self.render_design_task_system_message(*args, **kwargs)
        return {"system_msg": [system_msg.content], "human_msg": human_msg.content}
    
    def generate_task_if_inventory_full(self, events, chest_observation):
        """
        TODO: Try if this could be done with prompt
        Returns: Task When inventory is almost full
        """
        if chest_observation != "Chests: None\n\n":
            chests = chest_observation[8:-2].split("\n")
            for chest in chests:
                content = chest.split(":")[1]
                if content == " Unknown items inside" or content == " Empty":
                    position = chest.split(":")[0]
                    task = f"Deposit useless items into the chest at {position}"
                    return task
        if "chest" in events[-1][1]["inventory"]:
            task = "Place a chest"
        else:
            task = "Craft 1 chest"
        return task
    
    # -----------------------------------------------------------------------------------------
    
    # --------------------------------Design Curriculum Prepare--------------------------------
    def render_design_curriculum_system_message(self, *args, **kwargs):
        return SystemMessage(content=load_prompt("curriculum_qa_step1_ask_questions"))
    
    def render_design_curriculum_human_message(
            self, events, chest_observation, *args, **kwargs
    ):
        observation = self.render_curriculum_observation(
            events=events, chest_observation=chest_observation
        )
        content = ""
        for key in CURRICULUM_OB:
            content += observation[key]
        return HumanMessage(content=content)
    
    def encapsule_design_curriculum_message(
            self, events, chest_observation, *args, **kwargs
    ):
        human_msg = self.render_design_curriculum_human_message(
            events=events, chest_observation=chest_observation, *args, **kwargs
        )
        system_msg = self.render_design_curriculum_system_message(*args, **kwargs)
        return {"system_msg": [system_msg.content], "human_msg": human_msg.content}
    
    def generate_context_if_inventory_full(self, events, chest_observation):
        """
        TODO: Try if this could be done with prompt
        Returns: Context When inventory is almost full
        """
        inventoryUsed = events[-1][1]["status"]["inventoryUsed"]
        if chest_observation != "Chests: None\n\n":
            chests = chest_observation[8:-2].split("\n")
            for chest in chests:
                content = chest.split(":")[1]
                if content == " Unknown items inside" or content == " Empty":
                    context = (
                        f"Your inventory have {inventoryUsed} occupied slots before depositing. "
                        "After depositing, your inventory should only have 20 occupied slots. "
                        "You should deposit useless items such as andesite, dirt, cobblestone, etc. "
                        "Also, you can deposit low-level tools, "
                        "For example, if you have a stone pickaxe, you can deposit a wooden pickaxe. "
                        "Make sure the list of useless items are in your inventory "
                        "(do not list items already in the chest), "
                        "You can use bot.inventoryUsed() to check how many inventory slots are used."
                    )
                    return context
        if "chest" in events[-1][1]["inventory"]:
            context = (
                f"You have a chest in inventory, place it around you. "
                f"If chests is not None, or nearby blocks contains chest, this task is success."
            )
        else:
            context = "Craft 1 chest with 8 planks of any kind of wood."
        return context
    
    # -----------------------------------------------------------------------------------------
    
    async def handle_task_design(self, human_msg, system_msg, *args, **kwargs):
        """
        Args:
            human_msg:
            system_msg:
            *args:
            **kwargs:

        Returns:
        """
        events = self.game_memory.event
        chest_observation = self.game_memory.chest_observation
        inventoryUsed = events[-1][1]["status"]["inventoryUsed"]
        
        if self.game_memory.progress == 0:
            task = self.game_memory.current_task
        elif inventoryUsed >= 33:
            task = self.generate_task_if_inventory_full(
                self, events=events, chest_observation=chest_observation
            )
        else:
            task = await DesignTask().run(human_msg, system_msg, *args, **kwargs)
        logger.info(f"Handle_task_design result is Here: {task}")
        
        self.perform_game_info_callback(task, self.game_memory.update_task)
        return Message(
            content=f"{task}", instruct_content="task_design", role=self.profile
        )
    
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
        events = self.game_memory.event
        chest_observation = self.game_memory.chest_observation
        inventoryUsed = events[-1][1]["status"]["inventoryUsed"]
        task = self.game_memory.current_task
        
        if self.game_memory.progress == 0:
            context = self.game_memory.context
        elif inventoryUsed >= 33:
            context = self.generate_context_if_inventory_full(
                self, events=events, chest_observation=chest_observation
            )
        else:
            context = await self.DesignCurriculum().run(
                task, human_msg, system_msg, *args, **kwargs
            )
        
        self.perform_game_info_callback(context, self.game_memory.update_context)
        return Message(
            content=f"{context}",
            instruct_content="curriculum_design",
            role=self.profile,
        )
    
    async def _act(self) -> Message:
        todo = self._rc.todo
        logger.debug(f"Todo is {todo}")
        self.maintain_actions(todo)
        
        # 获取最新的游戏周边环境信息
        # events = await self._obtain_events()
        events = self.game_memory.event
        chest_observation = self.game_memory.chest_observation
        
        design_task_message = await self.encapsule_design_task_message(
            events, chest_observation
        )
        design_curriculum_message = self.encapsule_design_curriculum_message(
            events, chest_observation
        )
        
        handler_map = {
            DesignTask: self.handle_task_design,
            DesignCurriculum: self.handle_curriculum_design,
        }
        handler = handler_map.get(type(todo))
        if handler:
            if type(todo) == DesignTask:
                msg = await handler(**design_task_message)
            else:
                msg = await handler(**design_curriculum_message)
            msg.cause_by = type(todo)
            msg.round_id = self.round_id
            self._publish_message(msg)
            return msg
        
        raise ValueError(f"Unknown todo type: {type(todo)}")

# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:14
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from typing import Iterable, Dict, Any
from pydantic import BaseModel, Field
import requests
import json
import re

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.software_company import SoftwareCompany

from metagpt.actions.minecraft.player_action import PlayerActions
from metagpt.roles.minecraft.minecraft_base import Minecraft
from metagpt.environment import Environment
from metagpt.mineflayer_environment import MineflayerEnv
from metagpt.const import CKPT_DIR
from metagpt.actions.minecraft.control_primitives import load_skills_code


class GameEnvironment(BaseModel, arbitrary_types_allowed=True):
    """
    游戏环境的记忆，用于多个agent进行信息的共享和缓存，而不需要重复在自己的角色内维护缓存
    """

    event: dict[str, Any] = Field(default_factory=dict)
    current_task: str = Field(default="Mine 1 wood log")
    task_execution_time: float = Field(default=float)
    context: str = Field(
        default="You can mine one of oak, birch, spruce, jungle, acacia, dark oak, or mangrove logs."
    )
    code: str = Field(default="")
    program_name: str = Field(default="")
    critique: str = Field(default="")
    skills: dict = Field(default_factory=dict) # for skills.json
    retrieve_skills: list[str]  = Field(default_factory=list) 
    event_summary: str = Field(default="")

    qa_cache: dict[str, str] = Field(default_factory=dict)
    completed_tasks: list[str] = Field(default_factory=list)  # Critique things
    failed_tasks: list[str] = Field(default_factory=list)

    skill_desp: str = Field(default="")

    chest_memory: dict[str, Any] = Field(
        default_factory=dict
    )  # eg: {'(1344, 64, 1381)': 'Unknown'}
    chest_observation: str = Field(default="")  # eg: "Chests: None\n\n"

    mf_instance: MineflayerEnv = Field(default_factory=MineflayerEnv)

    @property
    def progress(self):
        # return len(self.completed_tasks) + 10 # Test only
        return len(self.completed_tasks)
    
    @property
    def programs(self):
        programs = ""
        if self.code == "":
            return programs # TODO: maybe fix 10054 now, a better way is isolating env.step() like voyager
        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"
        for primitives in load_skills_code():
            programs += f"{primitives}\n\n"
        return programs 

    @property
    def warm_up(self):
        return self.mf_instance.warm_up

    @property
    def core_inv_items_regex(self):
        return self.mf_instance.core_inv_items_regex

    def set_mc_port(self, mc_port):
        self.mf_instance.set_mc_port(mc_port)

    def set_mc_resume(self, resume: bool = False):  # TODO: mv to config
        if resume:
            logger.info(f"Loading Action Developer from {CKPT_DIR}/action")
            with open(f"{CKPT_DIR}/action/chest_memory.json", "r") as f:
                self.chest_memory = json.load(f)

            logger.info(f"Loading Curriculum Agent from {CKPT_DIR}/curriculum")
            with open(f"{CKPT_DIR}/curriculum/completed_tasks.json", "r") as f:
                self.completed_tasks = json.load(f)
            with open(f"{CKPT_DIR}/curriculum/failed_tasks.json", "r") as f:
                self.failed_tasks = json.load(f)
            with open(f"{CKPT_DIR}/curriculum/qa_cache.json", "r") as f:
                self.qa_cache = json.load(f)

            logger.info(f"Loading Skill Manager from {CKPT_DIR}/skill\033[0m")
            with open(f"{CKPT_DIR}/skill/skills.json", "r") as f:
                self.skills = json.load(f)

    def register_roles(self, roles: Iterable[Minecraft]):
        for role in roles:
            role.set_memory(self)

    def update_event(self, event: Dict):
        if self.event == event:
            return
        self.event = event
        self.update_chest_memory(event)
        self.event_summary = self.summarize_chatlog(event)

    def update_task(self, task: str):
        self.current_task = task

    def update_context(self, context: str):
        self.context = context

    def update_code(self, code: str):
        self.code = code  # action_developer.gen_action_code to HERE

    def update_program_name(self, program_name: str):
        self.program_name = program_name

    def update_critique(self, critique: str):
        self.critique = critique  # critic_agent.check_task_success to HERE

    def append_skill(self, skill: dict):
        self.skills[self.program_name] = skill  # skill_manager.retrieve_skills to HERE

    def update_retrieve_skills(self, retrieve_skills: list):
        self.retrieve_skills = retrieve_skills

    def update_skill_desp(self, skill_desp: str):
        self.skill_desp = skill_desp

    def update_chest_memory(self, events: Dict):
        """
        Input: events: Dict
        Result: self.chest_memory update & save to json
        """
        nearbyChests = events[-1][1]["nearbyChests"]
        for position, chest in nearbyChests.items():
            if position in self.chest_memory:
                if isinstance(chest, dict):
                    self.chest_memory[position] = chest
                if chest == "Invalid":
                    logger.info(f"Action Developer removing chest {position}: {chest}")
                    self.chest_memory.pop(position)
            else:
                if chest != "Invalid":
                    logger.info(f"Action Developer saving chest {position}: {chest}")
                    self.chest_memory[position] = chest
        with open(f"{CKPT_DIR}/action/chest_memory.json", "w") as f:
            json.dump(self.chest_memory, f)

    def update_chest_observation(self):
        """
        update chest_memory to chest_observation.
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/action.py
        """

        chests = []
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) > 0:
                chests.append(f"{chest_position}: {chest}")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) == 0:
                chests.append(f"{chest_position}: Empty")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, str):
                assert chest == "Unknown"
                chests.append(f"{chest_position}: Unknown items inside")
        assert len(chests) == len(self.chest_memory)
        if chests:
            chests = "\n".join(chests)
            self.chest_observation = f"Chests:\n{chests}\n\n"
        else:
            self.chest_observation = f"Chests: None\n\n"

    def summarize_chatlog(self, events):
        def filter_item(message: str):
            craft_pattern = r"I cannot make \w+ because I need: (.*)"
            craft_pattern2 = (
                r"I cannot make \w+ because there is no crafting table nearby"
            )
            mine_pattern = r"I need at least a (.*) to mine \w+!"
            if re.match(craft_pattern, message):
                return re.match(craft_pattern, message).groups()[0]
            elif re.match(craft_pattern2, message):
                return "a nearby crafting table"
            elif re.match(mine_pattern, message):
                return re.match(mine_pattern, message).groups()[0]
            else:
                return ""

        chatlog = set()
        for event_type, event in events:
            if event_type == "onChat":
                item = filter_item(event["onChat"])
                if item:
                    chatlog.add(item)
        return "I also need " + ", ".join(chatlog) + "." if chatlog else ""

    def update_exploration_progress(self, success: bool):
        """
        Split task into completed_tasks or failed_tasks
        Args: info = {
            "task": self.task,
            "success": success,
            "conversations": self.conversations,
        }
        """
        task = self.current_task
        if task.startswith("Deposit useless items into the chest at"):
            return
        if success:
            logger.info(f"Completed task {task}.")
            self.completed_tasks.append(task)
        else:
            logger.info(f"Failed to complete task {task}. Skipping to next task.")
            self.failed_tasks.append(task)
            # TODO: when not success, transform code below to update event!(isolate step soon!)
            # if self.reset_placed_if_failed and not success:
            #     # revert all the placing event in the last step
            #     blocks = []
            #     positions = []
            #     for event_type, event in events:
            #         if event_type == "onSave" and event["onSave"].endswith("_placed"):
            #             block = event["onSave"].split("_placed")[0]
            #             position = event["status"]["position"]
            #             blocks.append(block)
            #             positions.append(position)
            #     new_events = self.env.step(
            #         f"await givePlacedItemBack(bot, {U.json_dumps(blocks)}, {U.json_dumps(positions)})",
            #         programs=self.skill_manager.programs,
            #     )
            #     events[-1][1]["inventory"] = new_events[-1][1]["inventory"]
            #     events[-1][1]["voxels"] = new_events[-1][1]["voxels"]

        self.save_sorted_tasks()

    def save_sorted_tasks(self):
        updated_completed_tasks = []
        # record repeated failed tasks
        updated_failed_tasks = self.failed_tasks
        # dedup but keep order
        for task in self.completed_tasks:
            if task not in updated_completed_tasks:
                updated_completed_tasks.append(task)

        # remove completed tasks from failed tasks
        for task in updated_completed_tasks:
            while task in updated_failed_tasks:
                updated_failed_tasks.remove(task)

        self.completed_tasks = updated_completed_tasks
        self.failed_tasks = updated_failed_tasks

        # dump to json
        with open(f"{CKPT_DIR}/curriculum/completed_tasks.json", "w") as f:
            json.dump(self.completed_tasks, f)
        with open(f"{CKPT_DIR}/curriculum/failed_tasks.json", "w") as f:
            json.dump(self.failed_tasks, f)

    async def on_event(self, *args):
        """
        Retrieve Minecraft events.

        This function is used to obtain events from the Minecraft environment. Check the implementation in
        the 'voyager/env/bridge.py step()' function to capture events generated within the game.

        Returns:
            list: A list of Minecraft events.

            Raises:
                Exception: If there is an issue retrieving events.
        """
        try:
            if not self.mf_instance.has_reset:
                # TODO Modify
                logger.info("Environment has not been reset yet, is resetting")
                self.mf_instance.reset(
                    options={
                        "mode": "soft",
                        "wait_ticks": 20,
                    }
                )
                # raise {}
            self.mf_instance.check_process()
            self.mf_instance.unpause()
            data = {
                "code": self.code,
                "programs": self.programs,
            }
            res = requests.post(
                f"{self.mf_instance.server}/step",
                json=data,
                timeout=self.mf_instance.request_timeout,
            )
            if res.status_code != 200:
                logger.error("Failed to step Minecraft server")
                raise {}
            returned_data = res.json()
            self.mf_instance.pause()
            events = json.loads(returned_data)
            logger.info(f"Get Current Event: {events}")
            return events
        except Exception as e:
            logger.error(f"Failed to retrieve Minecraft events: {str(e)}")
            raise {}


class MinecraftPlayer(SoftwareCompany):
    """
    Software Company: Possesses a team, SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to writing executable code.
    """

    environment: Environment = Field(default_factory=Environment)
    game_memory: GameEnvironment = Field(default_factory=GameEnvironment)
    investment: float = Field(default=50.0)
    task: str = Field(default="")
    game_info: dict = Field(default={})

    def set_port(self, mc_port):
        self.game_memory.set_mc_port(mc_port)

    def set_resume(self, resume: bool = False):
        self.game_memory.set_mc_resume(resume=resume)
    
    def check_complete_round(self):
        complete_round = []
        for role in self.environment.roles.values():
            status = role.finish_step
            complete_round.append(status)
            #if not status:
            #    return complete_round
        #complete_round = True
        complete_round_tag = all(complete_round)
        logger.info(f"complete_round {complete_round}")
        return complete_round_tag
    
    def update_round(self):
        for role in self.environment.roles.values():
            role.finish_step = False
            role.round_id+=1
            role._rc.todo = None
            logger.info(f"round_id:{role.round_id}")

    def hire(self, roles: list[Role]):
        self.environment.add_roles(roles)
        self.game_memory.register_roles(roles)

    def start(self, task, round=0):
        """Start a project from publishing boss requirement."""
        self.task = task
        self.environment.publish_message(
            Message(role="Player", content=task, cause_by=PlayerActions, round_id=round)
        )
        logger.info(self.game_info)

    def _save(self):
        logger.info(self.json())
    
    def _reset(self):
        for role_profile, role in self.environment.roles.items():
            role.reset_state()

    async def run(self, n_round=3):
        """Run company until target round or no money"""
        round_id=0
        while n_round > 0:
            # self._save()
            if self.check_complete_round():
                n_round -= 1
                self.update_round()
                round_id+=1
                # add new task into env and continue
                #fixme: update self.task
                self.start(task=self.task, round=round_id)
                
            logger.info(f"{n_round=}")
            self._check_balance()
            await self.environment.run()
            #self.environment.memory.clear()
            #self._reset()
        return self.environment.history

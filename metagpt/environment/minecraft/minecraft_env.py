#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MG Minecraft Env
#           refs to `voyager voyager.py`

import json
import re
import time
from typing import Any, Iterable

from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import ConfigDict, Field

from metagpt.config2 import config as CONFIG
from metagpt.environment.base_env import Environment
from metagpt.environment.minecraft.const import MC_CKPT_DIR
from metagpt.environment.minecraft.minecraft_ext_env import MinecraftExtEnv
from metagpt.logs import logger
from metagpt.utils.common import load_mc_skills_code, read_json_file, write_json_file


class MinecraftEnv(MinecraftExtEnv, Environment):
    """MinecraftEnv, including shared memory of cache and information between roles"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    event: dict[str, Any] = Field(default_factory=dict)
    current_task: str = Field(default="Mine 1 wood log")
    task_execution_time: float = Field(default=float)
    context: str = Field(default="You can mine one of oak, birch, spruce, jungle, acacia, dark oak, or mangrove logs.")
    code: str = Field(default="")
    program_code: str = Field(default="")  # write in skill/code/*.js
    program_name: str = Field(default="")
    critique: str = Field(default="")
    skills: dict = Field(default_factory=dict)  # for skills.json
    retrieve_skills: list[str] = Field(default_factory=list)
    event_summary: str = Field(default="")

    qa_cache: dict[str, str] = Field(default_factory=dict)
    completed_tasks: list[str] = Field(default_factory=list)  # Critique things
    failed_tasks: list[str] = Field(default_factory=list)

    skill_desp: str = Field(default="")

    chest_memory: dict[str, Any] = Field(default_factory=dict)  # eg: {'(1344, 64, 1381)': 'Unknown'}
    chest_observation: str = Field(default="")  # eg: "Chests: None\n\n"

    runtime_status: bool = False  # equal to action execution status: success or failed

    vectordb: ChromaVectorStore = Field(default_factory=ChromaVectorStore)

    qa_cache_questions_vectordb: ChromaVectorStore = Field(default_factory=ChromaVectorStore)

    @property
    def progress(self):
        # return len(self.completed_tasks) + 10 # Test only
        return len(self.completed_tasks)

    @property
    def programs(self):
        programs = ""
        if self.code == "":
            return programs  # TODO: maybe fix 10054 now, a better way is isolating env.step() like voyager
        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"
        for primitives in load_mc_skills_code():  # TODO add skills_dir
            programs += f"{primitives}\n\n"
        return programs

    def set_mc_port(self, mc_port):
        super().set_mc_port(mc_port)
        self.set_mc_resume()

    def set_mc_resume(self):
        self.qa_cache_questions_vectordb = ChromaVectorStore(
            collection_name="qa_cache_questions_vectordb",
            persist_dir=f"{MC_CKPT_DIR}/curriculum/vectordb",
        )

        self.vectordb = ChromaVectorStore(
            collection_name="skill_vectordb",
            persist_dir=f"{MC_CKPT_DIR}/skill/vectordb",
        )

        if CONFIG.resume:
            logger.info(f"Loading Action Developer from {MC_CKPT_DIR}/action")
            self.chest_memory = read_json_file(f"{MC_CKPT_DIR}/action/chest_memory.json")

            logger.info(f"Loading Curriculum Agent from {MC_CKPT_DIR}/curriculum")
            self.completed_tasks = read_json_file(f"{MC_CKPT_DIR}/curriculum/completed_tasks.json")
            self.failed_tasks = read_json_file(f"{MC_CKPT_DIR}/curriculum/failed_tasks.json")

            logger.info(f"Loading Skill Manager from {MC_CKPT_DIR}/skill\033[0m")
            self.skills = read_json_file(f"{MC_CKPT_DIR}/skill/skills.json")

            logger.info(f"Loading Qa Cache from {MC_CKPT_DIR}/curriculum\033[0m")
            self.qa_cache = read_json_file(f"{MC_CKPT_DIR}/curriculum/qa_cache.json")

            if self.vectordb._collection.count() == 0:
                logger.info(self.vectordb._collection.count())
                # Set vdvs for skills & qa_cache
                skill_desps = [skill["description"] for program_name, skill in self.skills.items()]
                program_names = [program_name for program_name, skill in self.skills.items()]
                metadatas = [{"name": program_name} for program_name in program_names]
                # add vectordb from file
                self.vectordb.add_texts(
                    texts=skill_desps,
                    ids=program_names,
                    metadatas=metadatas,
                )
                self.vectordb.persist()

            logger.info(self.qa_cache_questions_vectordb._collection.count())
            if self.qa_cache_questions_vectordb._collection.count() == 0:
                questions = [question for question, answer in self.qa_cache.items()]

                self.qa_cache_questions_vectordb.add_texts(texts=questions)

                self.qa_cache_questions_vectordb.persist()

                logger.info(
                    f"INIT_CHECK: There are {self.vectordb._collection.count()} skills in vectordb and {len(self.skills)} skills in skills.json."
                )
                # Check if Skill Manager's vectordb right using
                assert self.vectordb._collection.count() == len(self.skills), (
                    f"Skill Manager's vectordb is not synced with skills.json.\n"
                    f"There are {self.vectordb._collection.count()} skills in vectordb but {len(self.skills)} skills in skills.json.\n"
                    f"Did you set resume=False when initializing the manager?\n"
                    f"You may need to manually delete the vectordb directory for running from scratch."
                )

                logger.info(
                    f"INIT_CHECK: There are {self.qa_cache_questions_vectordb._collection.count()} qa_cache in vectordb and {len(self.qa_cache)} questions in qa_cache.json."
                )
                assert self.qa_cache_questions_vectordb._collection.count() == len(self.qa_cache), (
                    f"Curriculum Agent's qa cache question vectordb is not synced with qa_cache.json.\n"
                    f"There are {self.qa_cache_questions_vectordb._collection.count()} questions in vectordb "
                    f"but {len(self.qa_cache)} questions in qa_cache.json.\n"
                    f"Did you set resume=False when initializing the agent?\n"
                    f"You may need to manually delete the qa cache question vectordb directory for running from scratch.\n"
                )

    def register_roles(self, roles: Iterable["Minecraft"]):
        for role in roles:
            role.set_memory(self)

    def update_event(self, event: dict):
        if self.event == event:
            return
        self.event = event
        self.update_chest_memory(event)
        self.update_chest_observation()
        # self.event_summary = self.summarize_chatlog(event)

    def update_task(self, task: str):
        self.current_task = task

    def update_context(self, context: str):
        self.context = context

    def update_program_code(self, program_code: str):
        self.program_code = program_code

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

    async def update_qa_cache(self, qa_cache: dict):
        self.qa_cache = qa_cache

    def update_chest_memory(self, events: dict):
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

        write_json_file(f"{MC_CKPT_DIR}/action/chest_memory.json", self.chest_memory)

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
            self.chest_observation = "Chests: None\n\n"

    def summarize_chatlog(self, events):
        def filter_item(message: str):
            craft_pattern = r"I cannot make \w+ because I need: (.*)"
            craft_pattern2 = r"I cannot make \w+ because there is no crafting table nearby"
            mine_pattern = r"I need at least a (.*) to mine \w+!"
            if re.match(craft_pattern, message):
                self.event_summary = re.match(craft_pattern, message).groups()[0]
            elif re.match(craft_pattern2, message):
                self.event_summary = "a nearby crafting table"
            elif re.match(mine_pattern, message):
                self.event_summary = re.match(mine_pattern, message).groups()[0]
            else:
                self.event_summary = ""
            return self.event_summary

        chatlog = set()
        for event_type, event in events:
            if event_type == "onChat":
                item = filter_item(event["onChat"])
                if item:
                    chatlog.add(item)
        self.event_summary = "I also need " + ", ".join(chatlog) + "." if chatlog else ""

    def reset_block_info(self):
        # revert all the placing event in the last step
        pass

    def update_exploration_progress(self, success: bool):
        """
        Split task into completed_tasks or failed_tasks
        Args: info = {
            "task": self.task,
            "success": success,
            "conversations": self.conversations,
        }
        """
        self.runtime_status = success
        task = self.current_task
        if task.startswith("Deposit useless items into the chest at"):
            return
        if success:
            logger.info(f"Completed task {task}.")
            self.completed_tasks.append(task)
        else:
            logger.info(f"Failed to complete task {task}. Skipping to next task.")
            self.failed_tasks.append(task)
            # when not success, below to update event!
            # revert all the placing event in the last step
            blocks = []
            positions = []
            for event_type, event in self.event:
                if event_type == "onSave" and event["onSave"].endswith("_placed"):
                    block = event["onSave"].split("_placed")[0]
                    position = event["status"]["position"]
                    blocks.append(block)
                    positions.append(position)
            new_events = self._step(
                f"await givePlacedItemBack(bot, {json.dumps(blocks)}, {json.dumps(positions)})",
                programs=self.programs,
            )
            self.event[-1][1]["inventory"] = new_events[-1][1]["inventory"]
            self.event[-1][1]["voxels"] = new_events[-1][1]["voxels"]

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
        write_json_file(f"{MC_CKPT_DIR}/curriculum/completed_tasks.json", self.completed_tasks)
        write_json_file(f"{MC_CKPT_DIR}/curriculum/failed_tasks.json", self.failed_tasks)

    async def on_event_retrieve(self, *args):
        """
        Retrieve Minecraft events.

        Returns:
            list: A list of Minecraft events.

            Raises:
                Exception: If there is an issue retrieving events.
        """
        try:
            self._reset(
                options={
                    "mode": "soft",
                    "wait_ticks": 20,
                }
            )
            # difficulty = "easy" if len(self.completed_tasks) > 15 else "peaceful"
            difficulty = "peaceful"

            events = self._step("bot.chat(`/time set ${getNextTime()}`);\n" + f"bot.chat('/difficulty {difficulty}');")
            self.update_event(events)
            return events
        except Exception as e:
            time.sleep(3)  # wait for mineflayer to exit
            # reset bot status here
            events = self._reset(
                options={
                    "mode": "hard",
                    "wait_ticks": 20,
                    "inventory": self.event[-1][1]["inventory"],
                    "equipment": self.event[-1][1]["status"]["equipment"],
                    "position": self.event[-1][1]["status"]["position"],
                }
            )
            self.update_event(events)
            logger.error(f"Failed to retrieve Minecraft events: {str(e)}")
            return events

    async def on_event_execute(self, *args):
        """
        Execute Minecraft events.

        This function is used to obtain events from the Minecraft environment. Check the implementation in
        the 'voyager/env/bridge.py step()' function to capture events generated within the game.

        Returns:
            list: A list of Minecraft events.

            Raises:
                Exception: If there is an issue retrieving events.
        """
        try:
            events = self._step(
                code=self.code,
                programs=self.programs,
            )
            self.update_event(events)
            return events
        except Exception as e:
            time.sleep(3)  # wait for mineflayer to exit
            # reset bot status here
            events = self._reset(
                options={
                    "mode": "hard",
                    "wait_ticks": 20,
                    "inventory": self.event[-1][1]["inventory"],
                    "equipment": self.event[-1][1]["status"]["equipment"],
                    "position": self.event[-1][1]["status"]["position"],
                }
            )
            self.update_event(events)
            logger.error(f"Failed to execute Minecraft events: {str(e)}")
            return events

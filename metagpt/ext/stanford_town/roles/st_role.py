#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Stanford Town role

"""
Do the steps following:
- perceive, receive environment(Maze) info
- retrieve, retrieve memories
- plan, do plan like long-term plan and interact with Maze
- reflect, do the High-level thinking based on memories and re-add into the memory
- execute, move or else in the Maze
"""
import math
import random
import time
from datetime import datetime, timedelta
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator

from metagpt.actions.add_requirement import UserRequirement
from metagpt.environment.stanford_town.env_space import (
    EnvAction,
    EnvActionType,
    EnvObsParams,
    EnvObsType,
)
from metagpt.ext.stanford_town.actions.dummy_action import DummyAction, DummyMessage
from metagpt.ext.stanford_town.actions.inner_voice_action import (
    AgentWhisperThoughtAction,
)
from metagpt.ext.stanford_town.actions.run_reflect_action import AgentEventTriple
from metagpt.ext.stanford_town.memory.agent_memory import AgentMemory, BasicMemory
from metagpt.ext.stanford_town.memory.scratch import Scratch
from metagpt.ext.stanford_town.memory.spatial_memory import MemoryTree
from metagpt.ext.stanford_town.plan.st_plan import plan
from metagpt.ext.stanford_town.reflect.reflect import generate_poig_score, role_reflect
from metagpt.ext.stanford_town.utils.const import STORAGE_PATH, collision_block_id
from metagpt.ext.stanford_town.utils.mg_ga_transform import (
    get_role_environment,
    save_environment,
    save_movement,
)
from metagpt.ext.stanford_town.utils.utils import get_embedding, path_finder
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleContext
from metagpt.schema import Message
from metagpt.utils.common import any_to_str

if TYPE_CHECKING:
    from metagpt.environment.stanford_town.stanford_town_env import (  # noqa: F401
        StanfordTownEnv,
    )


class STRoleContext(RoleContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    env: "StanfordTownEnv" = Field(default=None, exclude=True)
    memory: AgentMemory = Field(default_factory=AgentMemory)
    scratch: Scratch = Field(default_factory=Scratch)
    spatial_memory: MemoryTree = Field(default_factory=MemoryTree)

    @classmethod
    def model_rebuild(cls, **kwargs):
        from metagpt.environment.stanford_town.stanford_town_env import (  # noqa: F401
            StanfordTownEnv,
        )

        super(RoleContext, cls).model_rebuild(**kwargs)


class STRole(Role):
    # add a role's property structure to store role's age and so on like GA's Scratch.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="Klaus Mueller")
    profile: str = Field(default="STMember")

    rc: STRoleContext = Field(default_factory=STRoleContext)

    sim_code: str = Field(default="new_sim")
    step: int = Field(default=0)
    start_time: Optional[datetime] = Field(default=None)
    curr_time: Optional[datetime] = Field(default=None)
    sec_per_step: int = Field(default=10)
    game_obj_cleanup: dict = Field(default_factory=dict)
    inner_voice: bool = Field(default=False)
    has_inner_voice: bool = Field(default=False)

    role_storage_path: Optional[Path] = Field(default=None)

    @field_validator("curr_time", mode="before")
    @classmethod
    def check_curr_time(cls, curr_time: str) -> datetime:
        return datetime.strptime(curr_time, "%B %d, %Y, %H:%M:%S")

    @field_validator("start_time", mode="before")
    @classmethod
    def check_start_time(cls, start_time: str) -> datetime:
        return datetime.strptime(f"{start_time}, 00:00:00", "%B %d, %Y, %H:%M:%S")

    @model_validator(mode="after")
    def validate_st_role_after(self):
        self.role_storage_path = STORAGE_PATH.joinpath(f"{self.sim_code}/personas/{self.name}")

        self.load_from()  # load role's memory

        self.set_actions([])

        if self.has_inner_voice:
            # TODO add communication action
            self._watch([UserRequirement, DummyAction])
        else:
            self._watch([DummyAction])

    async def init_curr_tile(self):
        # init role
        role_env: dict = get_role_environment(self.sim_code, self.name, self.step)
        pt_x = role_env["x"]
        pt_y = role_env["y"]
        self.rc.scratch.curr_tile = (pt_x, pt_y)

        self.rc.env.step(
            EnvAction(
                action_type=EnvActionType.ADD_TILE_EVENT,
                coord=(pt_x, pt_y),
                event=self.scratch.get_curr_event_and_desc(),
            )
        )

    @property
    def scratch(self):
        return self.rc.scratch

    @property
    def role_tile(self):
        return self.scratch.curr_tile

    @property
    def a_mem(self):
        return self.rc.memory

    @property
    def s_mem(self):
        return self.rc.spatial_memory

    @property
    def memory(self):
        return self.rc.memory

    def load_from(self):
        """
        load role data from `storage/{simulation_name}/personas/{role_name}`
        """
        memory_saved = self.role_storage_path.joinpath("bootstrap_memory/associative_memory")
        self.rc.memory.set_mem_path(memory_saved)

        sp_mem_saved = self.role_storage_path.joinpath("bootstrap_memory/spatial_memory.json")
        self.rc.spatial_memory.set_mem_path(f_saved=sp_mem_saved)

        scratch_f_saved = self.role_storage_path.joinpath("bootstrap_memory/scratch.json")
        self.rc.scratch = Scratch.init_scratch_from_path(f_saved=scratch_f_saved)

        logger.info(f"Role: {self.name} loaded role's memory from {str(self.role_storage_path)}")

    def save_into(self):
        """
        save role data from `storage/{simulation_name}/personas/{role_name}`
        """
        memory_saved = self.role_storage_path.joinpath("bootstrap_memory/associative_memory")
        self.rc.memory.save(memory_saved)

        sp_mem_saved = self.role_storage_path.joinpath("bootstrap_memory/spatial_memory.json")
        self.rc.spatial_memory.save(sp_mem_saved)

        scratch_f_saved = self.role_storage_path.joinpath("bootstrap_memory/scratch.json")
        self.rc.scratch.save(scratch_f_saved)

        logger.info(f"Role: {self.name} saved role's memory into {str(self.role_storage_path)}")

    async def _observe(self, ignore_memory=False) -> int:
        if not self.rc.env:
            return 0
        news = []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        old_messages = [] if ignore_memory else self.rc.memory.get()
        # Filter out messages of interest.
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.name in n.send_to) and n not in old_messages
        ]

        if len(self.rc.news) == 1 and self.rc.news[0].cause_by == any_to_str(UserRequirement):
            logger.warning(f"Role: {self.name} add inner voice: {self.rc.news[0].content}")
            await self.add_inner_voice(self.rc.news[0].content)

        return 1  # always return 1 to execute role's `_react`

    async def add_inner_voice(self, whisper: str):
        async def generate_inner_thought(whisper: str):
            run_whisper_thought = AgentWhisperThoughtAction()
            inner_thought = await run_whisper_thought.run(self, whisper)
            return inner_thought

        thought = await generate_inner_thought(whisper)

        # init scratch curr_time with self.curr_time
        self.inner_voice = True
        self.rc.scratch.curr_time = self.curr_time

        created = self.rc.scratch.curr_time if self.rc.scratch.curr_time else datetime.now()
        expiration = created + timedelta(days=30)
        run_event_triple = AgentEventTriple()
        s, p, o = await run_event_triple.run(thought, self)
        keywords = set([s, p, o])
        thought_poignancy = await generate_poig_score(self, "event", whisper)
        thought_embedding_pair = (thought, get_embedding(thought))
        self.rc.memory.add_thought(
            created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, None
        )

    async def observe(self) -> list[BasicMemory]:
        # TODO observe info from maze_env
        """
        Perceive events around the role and saves it to the memory, both events
        and spaces.

        We first perceive the events nearby the role, as determined by its
        <vision_r>. If there are a lot of events happening within that radius, we
        take the <att_bandwidth> of the closest events. Finally, we check whether
        any of them are new, as determined by <retention>. If they are new, then we
        save those and return the <BasicMemory> instances for those events.

        OUTPUT:
            ret_events: a list of <BasicMemory> that are perceived and new.
        """
        # PERCEIVE SPACE
        # We get the nearby tiles given our current tile and the persona's vision
        # radius.
        nearby_tiles = self.rc.env.observe(
            EnvObsParams(
                obs_type=EnvObsType.TILE_NBR, coord=self.rc.scratch.curr_tile, vision_radius=self.rc.scratch.vision_r
            )
        )

        # We then store the perceived space. Note that the s_mem of the persona is
        # in the form of a tree constructed using dictionaries.
        for tile in nearby_tiles:
            tile_info = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=tile))
            self.rc.spatial_memory.add_tile_info(tile_info)

        # PERCEIVE EVENTS.
        # We will perceive events that take place in the same arena as the
        # persona's current arena.

        curr_arena_path = self.rc.env.observe(
            EnvObsParams(obs_type=EnvObsType.TILE_PATH, coord=self.rc.scratch.curr_tile, level="arena")
        )

        # We do not perceive the same event twice (this can happen if an object is
        # extended across multiple tiles).
        percept_events_set = set()
        # We will order our percept based on the distance, with the closest ones
        # getting priorities.
        percept_events_list = []
        # First, we put all events that are occuring in the nearby tiles into the
        # percept_events_list
        for tile in nearby_tiles:
            tile_details = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=tile))
            if tile_details["events"]:
                tmp_arena_path = self.rc.env.observe(
                    EnvObsParams(obs_type=EnvObsType.TILE_PATH, coord=tile, level="arena")
                )

                if tmp_arena_path == curr_arena_path:
                    # This calculates the distance between the persona's current tile,
                    # and the target tile.
                    dist = math.dist([tile[0], tile[1]], [self.rc.scratch.curr_tile[0], self.rc.scratch.curr_tile[1]])
                    # Add any relevant events to our temp set/list with the distant info.
                    for event in tile_details["events"]:
                        if event not in percept_events_set:
                            percept_events_list += [[dist, event]]
                            percept_events_set.add(event)

        # We sort, and perceive only self.rc.scratch.att_bandwidth of the closest
        # events. If the bandwidth is larger, then it means the persona can perceive
        # more elements within a small area.
        percept_events_list = sorted(percept_events_list, key=itemgetter(0))
        perceived_events = []
        for dist, event in percept_events_list[: self.rc.scratch.att_bandwidth]:
            perceived_events += [event]

        # Storing events.
        # <ret_events> is a list of <BasicMemory> instances from the persona's
        # associative memory.
        ret_events = []
        for p_event in perceived_events:
            s, p, o, desc = p_event
            if not p:
                # If the object is not present, then we default the event to "idle".
                p = "is"
                o = "idle"
                desc = "idle"
            desc = f"{s.split(':')[-1]} is {desc}"
            p_event = (s, p, o)

            # We retrieve the latest self.rc.scratch.retention events. If there is
            # something new that is happening (that is, p_event not in latest_events),
            # then we add that event to the a_mem and return it.
            latest_events = self.rc.memory.get_summarized_latest_events(self.rc.scratch.retention)
            if p_event not in latest_events:
                # We start by managing keywords.
                keywords = set()
                sub = p_event[0]
                obj = p_event[2]
                if ":" in p_event[0]:
                    sub = p_event[0].split(":")[-1]
                if ":" in p_event[2]:
                    obj = p_event[2].split(":")[-1]
                keywords.update([sub, obj])

                # Get event embedding
                desc_embedding_in = desc
                if "(" in desc:
                    desc_embedding_in = desc_embedding_in.split("(")[1].split(")")[0].strip()
                if desc_embedding_in in self.rc.memory.embeddings:
                    event_embedding = self.rc.memory.embeddings[desc_embedding_in]
                else:
                    event_embedding = get_embedding(desc_embedding_in)
                event_embedding_pair = (desc_embedding_in, event_embedding)

                # Get event poignancy.
                event_poignancy = await generate_poig_score(self, "event", desc_embedding_in)
                logger.debug(f"Role {self.name} event_poignancy: {event_poignancy}")

                # If we observe the persona's self chat, we include that in the memory
                # of the persona here.
                chat_node_ids = []
                if p_event[0] == f"{self.name}" and p_event[1] == "chat with":
                    curr_event = self.rc.scratch.act_event
                    if self.rc.scratch.act_description in self.rc.memory.embeddings:
                        chat_embedding = self.rc.memory.embeddings[self.rc.scratch.act_description]
                    else:
                        chat_embedding = get_embedding(self.rc.scratch.act_description)
                    chat_embedding_pair = (self.rc.scratch.act_description, chat_embedding)
                    chat_poignancy = await generate_poig_score(self, "chat", self.rc.scratch.act_description)
                    chat_node = self.rc.memory.add_chat(
                        self.rc.scratch.curr_time,
                        None,
                        curr_event[0],
                        curr_event[1],
                        curr_event[2],
                        self.rc.scratch.act_description,
                        keywords,
                        chat_poignancy,
                        chat_embedding_pair,
                        self.rc.scratch.chat,
                    )
                    chat_node_ids = [chat_node.memory_id]

                # Finally, we add the current event to the agent's memory.
                ret_events += [
                    self.rc.memory.add_event(
                        self.rc.scratch.curr_time,
                        None,
                        s,
                        p,
                        o,
                        desc,
                        keywords,
                        event_poignancy,
                        event_embedding_pair,
                        chat_node_ids,
                    )
                ]
                self.rc.scratch.importance_trigger_curr -= event_poignancy
                self.rc.scratch.importance_ele_n += 1

        return ret_events

    def retrieve(self, observed: list) -> dict:
        # TODO retrieve memories from agent_memory
        retrieved = dict()
        for event in observed:
            retrieved[event.description] = dict()
            retrieved[event.description]["curr_event"] = event

            relevant_events = self.rc.memory.retrieve_relevant_events(event.subject, event.predicate, event.object)
            retrieved[event.description]["events"] = list(relevant_events)

            relevant_thoughts = self.rc.memory.retrieve_relevant_thoughts(event.subject, event.predicate, event.object)
            retrieved[event.description]["thoughts"] = list(relevant_thoughts)

        return retrieved

    async def reflect(self):
        # TODO reflection if meet reflect condition
        await role_reflect(self)
        # TODO re-add result to memory
        # 已封装到Reflect函数之中

    async def execute(self, plan: str):
        """
        Args:
            plan: This is a string address of the action we need to execute.
            It comes in the form of "{world}:{sector}:{arena}:{game_objects}".
            It is important that you access this without doing negative
            indexing (e.g., [-1]) because the latter address elements may not be
            present in some cases.
            e.g., "dolores double studio:double studio:bedroom 1:bed"
        """
        roles = self.rc.env.get_roles()
        if "<random>" in plan and self.rc.scratch.planned_path == []:
            self.rc.scratch.act_path_set = False

        # <act_path_set> is set to True if the path is set for the current action.
        # It is False otherwise, and means we need to construct a new path.
        if not self.rc.scratch.act_path_set:
            # <target_tiles> is a list of tile coordinates where the persona may go
            # to execute the current action. The goal is to pick one of them.
            target_tiles = None
            logger.info(f"Role {self.name} plan: {plan}")

            if "<persona>" in plan:
                # Executing persona-persona interaction.
                target_p_tile = roles[plan.split("<persona>")[-1].strip()].scratch.curr_tile
                collision_maze = self.rc.env.observe()["collision_maze"]
                potential_path = path_finder(
                    collision_maze, self.rc.scratch.curr_tile, target_p_tile, collision_block_id
                )
                if len(potential_path) <= 2:
                    target_tiles = [potential_path[0]]
                else:
                    collision_maze = self.rc.env.observe()["collision_maze"]
                    potential_1 = path_finder(
                        collision_maze,
                        self.rc.scratch.curr_tile,
                        potential_path[int(len(potential_path) / 2)],
                        collision_block_id,
                    )

                    potential_2 = path_finder(
                        collision_maze,
                        self.rc.scratch.curr_tile,
                        potential_path[int(len(potential_path) / 2) + 1],
                        collision_block_id,
                    )
                    if len(potential_1) <= len(potential_2):
                        target_tiles = [potential_path[int(len(potential_path) / 2)]]
                    else:
                        target_tiles = [potential_path[int(len(potential_path) / 2 + 1)]]

            elif "<waiting>" in plan:
                # Executing interaction where the persona has decided to wait before
                # executing their action.
                x = int(plan.split()[1])
                y = int(plan.split()[2])
                target_tiles = [[x, y]]

            elif "<random>" in plan:
                # Executing a random location action.
                plan = ":".join(plan.split(":")[:-1])

                address_tiles = self.rc.env.observe()["address_tiles"]
                target_tiles = address_tiles[plan]
                target_tiles = random.sample(list(target_tiles), 1)

            else:
                # This is our default execution. We simply take the persona to the
                # location where the current action is taking place.
                # Retrieve the target addresses. Again, plan is an action address in its
                # string form. <maze.address_tiles> takes this and returns candidate
                # coordinates.
                address_tiles = self.rc.env.observe()["address_tiles"]
                if plan not in address_tiles:
                    address_tiles["Johnson Park:park:park garden"]  # ERRORRRRRRR
                else:
                    target_tiles = address_tiles[plan]

            # There are sometimes more than one tile returned from this (e.g., a tabe
            # may stretch many coordinates). So, we sample a few here. And from that
            # random sample, we will take the closest ones.
            if len(target_tiles) < 4:
                target_tiles = random.sample(list(target_tiles), len(target_tiles))
            else:
                target_tiles = random.sample(list(target_tiles), 4)
            # If possible, we want personas to occupy different tiles when they are
            # headed to the same location on the maze. It is ok if they end up on the
            # same time, but we try to lower that probability.
            # We take care of that overlap here.
            persona_name_set = set(roles.keys())
            new_target_tiles = []
            for i in target_tiles:
                access_tile = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=i))
                curr_event_set = access_tile["events"]
                pass_curr_tile = False
                for j in curr_event_set:
                    if j[0] in persona_name_set:
                        pass_curr_tile = True
                if not pass_curr_tile:
                    new_target_tiles += [i]
            if len(new_target_tiles) == 0:
                new_target_tiles = target_tiles
            target_tiles = new_target_tiles

            # Now that we've identified the target tile, we find the shortest path to
            # one of the target tiles.
            curr_tile = self.rc.scratch.curr_tile
            closest_target_tile = None
            path = None
            for i in target_tiles:
                # path_finder takes a collision_mze and the curr_tile coordinate as
                # an input, and returns a list of coordinate tuples that becomes the
                # path.
                # e.g., [(0, 1), (1, 1), (1, 2), (1, 3), (1, 4)...]
                collision_maze = self.rc.env.observe()["collision_maze"]
                curr_path = path_finder(collision_maze, curr_tile, i, collision_block_id)
                if not closest_target_tile:
                    closest_target_tile = i
                    path = curr_path
                elif len(curr_path) < len(path):
                    closest_target_tile = i
                    path = curr_path

            # Actually setting the <planned_path> and <act_path_set>. We cut the
            # first element in the planned_path because it includes the curr_tile.
            self.rc.scratch.planned_path = path[1:]
            self.rc.scratch.act_path_set = True

        # Setting up the next immediate step. We stay at our curr_tile if there is
        # no <planned_path> left, but otherwise, we go to the next tile in the path.
        ret = self.rc.scratch.curr_tile
        if self.rc.scratch.planned_path:
            ret = self.rc.scratch.planned_path[0]
            self.rc.scratch.planned_path = self.rc.scratch.planned_path[1:]

        description = f"{self.rc.scratch.act_description}"
        description += f" @ {self.rc.scratch.act_address}"

        execution = ret, self.rc.scratch.act_pronunciatio, description
        return execution

    async def update_role_env(self) -> bool:
        role_env = get_role_environment(self.sim_code, self.name, self.step)
        ret = True
        if role_env:
            for key, val in self.game_obj_cleanup.items():
                self.rc.env.step(EnvAction(action_type=EnvActionType.TURN_TILE_EVENT_IDLE, coord=val, event=key))

            # reset game_obj_cleanup
            self.game_obj_cleanup = dict()
            curr_tile = self.role_tile
            new_tile = (role_env["x"], role_env["y"])
            self.rc.env.step(
                EnvAction(action_type=EnvActionType.RM_TITLE_SUB_EVENT, coord=curr_tile, subject=self.name)
            )
            self.rc.env.step(
                EnvAction(
                    action_type=EnvActionType.ADD_TILE_EVENT,
                    coord=new_tile,
                    event=self.scratch.get_curr_event_and_desc(),
                )
            )

            # the persona will travel to get to their destination. *Once*
            # the persona gets there, we activate the object action.
            if not self.scratch.planned_path:
                self.game_obj_cleanup[self.scratch.get_curr_event_and_desc()] = new_tile
                self.rc.env.step(
                    EnvAction(
                        action_type=EnvActionType.ADD_TILE_EVENT,
                        coord=new_tile,
                        event=self.scratch.get_curr_event_and_desc(),
                    )
                )

                blank = (self.scratch.get_curr_obj_event_and_desc()[0], None, None, None)
                self.rc.env.step(EnvAction(action_type=EnvActionType.RM_TILE_EVENT, coord=new_tile, event=blank))

            # update role's new tile
            self.rc.scratch.curr_tile = new_tile
        else:
            ret = False
            time.sleep(1)
            logger.warning(
                f"{self.sim_code}/environment/{self.step}.json not exist or parses failed, " f"sleep 1s and re-check"
            )
        return ret

    async def _react(self) -> Message:
        # update role env
        ret = await self.update_role_env()
        if not ret:
            # TODO add message
            logger.info(f"Role: {self.name} update_role_env return False")
            return DummyMessage()

        new_day = False
        if not self.scratch.curr_time or self.inner_voice:
            new_day = "First day"
        elif self.scratch.curr_time.strftime("%A %B %d") != self.curr_time.strftime("%A %B %d"):
            new_day = "New day"
        logger.info(f"Role: {self.name} new_day: {new_day}")
        self.rc.scratch.curr_time = self.curr_time

        # get maze_env from self.rc.env, and observe env info
        observed = await self.observe()

        # use self.rc.memory 's retrieve functions
        retrieved = self.retrieve(observed)

        plans = await plan(self, self.rc.env.get_roles(), new_day, retrieved)

        await self.reflect()

        # feed-back into maze_env
        next_tile, pronunciatio, description = await self.execute(plans)
        role_move = {
            "movement": next_tile,
            "pronunciatio": pronunciatio,
            "description": description,
            "chat": self.scratch.chat,
        }
        save_movement(self.name, role_move, step=self.step, sim_code=self.sim_code, curr_time=self.curr_time)

        # step update
        logger.info(f"Role: {self.name} run at {self.step} step on {self.curr_time} at tile: {self.scratch.curr_tile}")
        self.step += 1
        save_environment(self.name, self.step, self.sim_code, next_tile)
        self.curr_time += timedelta(seconds=self.sec_per_step)
        self.inner_voice = False

        time.sleep(0.5)
        return DummyMessage()


STRoleContext.model_rebuild()

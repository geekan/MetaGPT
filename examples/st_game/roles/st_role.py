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
import time

from pydantic import Field
from pathlib import Path
import random
import datetime
from operator import itemgetter

from metagpt.roles.role import Role, RoleContext
from metagpt.schema import Message
from metagpt.logs import logger

from ..memory.agent_memory import AgentMemory, BasicMemory
from ..memory.spatial_memory import MemoryTree
from ..actions.dummy_action import DummyAction
from ..actions.user_requirement import UserRequirement
from ..maze_environment import MazeEnvironment
from ..memory.retrieve import new_agent_retrieve
from ..memory.scratch import Scratch
from ..utils.utils import get_embedding, generate_poig_score, path_finder
from ..utils.const import collision_block_id
from ..reflect.st_reflect import agent_reflect
from ..utils.mg_ga_transform import save_movement, get_role_environment


class STRoleContext(RoleContext):
    env: 'MazeEnvironment' = Field(default=MazeEnvironment)
    memory: AgentMemory = Field(default=AgentMemory)
    scratch: Scratch = Field(default=Scratch)
    spatial_memory: MemoryTree = Field(default=MemoryTree)


class STRole(Role):
    # 继承Role类，Role类继承RoleContext，这里的逻辑需要认真考虑
    # add a role's property structure to store role's age and so on like GA's Scratch.

    def __init__(self,
                 name: str = "Klaus Mueller",
                 profile: str = "STMember",
                 sim_code: str = "new_sim",
                 step: int = 0,
                 start_date: str = "",
                 curr_time: str = "",
                 sec_per_step: int = 10,
                 has_inner_voice: bool = False):
        self.sim_code = sim_code
        self.step = step
        self.start_time = datetime.datetime.strptime(f"{start_date}, 00:00:00", "%B %d, %Y, %H:%M:%S")
        self.curr_time = datetime.datetime.strptime(curr_time, "%B %d, %Y, %H:%M:%S")
        self.sec_per_step = sec_per_step

        self.role_tile = (0, 0)
        self.game_obj_cleanup = dict()

        self._rc = STRoleContext()
        super(STRole, self).__init__(name=name,
                                     profile=profile)

        self._init_actions([])

        if has_inner_voice:
            # TODO add communication action
            self._watch([UserRequirement, DummyAction])
        else:
            self._watch([DummyAction])

        # init role & maze
        role_env = get_role_environment(self.sim_code, self.name, self.step)
        pt_x = role_env["x"]
        pt_y = role_env["y"]
        self.role_tile = (pt_x, pt_y)
        self._rc.env.maze.tiles[pt_y][pt_x]["events"].add(self.scratch.get_curr_event_and_desc())

    @property
    def name(self):
        return self._setting.name

    @property
    def scratch(self):
        return self._rc.scratch

    def load_from(self, folder: Path):
        """
        load role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass

    def save_into(self, folder: Path):
        """
        save role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass

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
        maze = self._rc.env.maze
        # PERCEIVE SPACE
        # We get the nearby tiles given our current tile and the persona's vision
        # radius.
        nearby_tiles = maze.get_nearby_tiles(self._rc.scratch.curr_tile,
                                             self._rc.scratch.vision_r)

        # We then store the perceived space. Note that the s_mem of the persona is
        # in the form of a tree constructed using dictionaries.
        for tile in nearby_tiles:
            tile_info = maze.access_tile(tile)
            self._rc.spatial_memory.add_tile_info(tile_info)

        # PERCEIVE EVENTS.
        # We will perceive events that take place in the same arena as the
        # persona's current arena.
        curr_arena_path = maze.get_tile_path(self._rc.scratch.curr_tile, "arena")
        # We do not perceive the same event twice (this can happen if an object is
        # extended across multiple tiles).
        percept_events_set = set()
        # We will order our percept based on the distance, with the closest ones
        # getting priorities.
        percept_events_list = []
        # First, we put all events that are occuring in the nearby tiles into the
        # percept_events_list
        for tile in nearby_tiles:
            tile_details = maze.access_tile(tile)
            if tile_details["events"]:
                if maze.get_tile_path(tile, "arena") == curr_arena_path:
                    # This calculates the distance between the persona's current tile,
                    # and the target tile.
                    dist = math.dist([tile[0], tile[1]],
                                     [self._rc.scratch.curr_tile[0],
                                      self._rc.scratch.curr_tile[1]])
                    # Add any relevant events to our temp set/list with the distant info.
                    for event in tile_details["events"]:
                        if event not in percept_events_set:
                            percept_events_list += [[dist, event]]
                            percept_events_set.add(event)

        # We sort, and perceive only self._rc.scratch.att_bandwidth of the closest
        # events. If the bandwidth is larger, then it means the persona can perceive
        # more elements within a small area.
        percept_events_list = sorted(percept_events_list, key=itemgetter(0))
        perceived_events = []
        for dist, event in percept_events_list[:self._rc.scratch.att_bandwidth]:
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

            # We retrieve the latest self._rc.scratch.retention events. If there is
            # something new that is happening (that is, p_event not in latest_events),
            # then we add that event to the a_mem and return it.
            latest_events = self._rc.memory.get_summarized_latest_events(
                self._rc.scratch.retention)
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
                desc_embedding_in = (desc_embedding_in.split("(")[1]
                                     .split(")")[0]
                                     .strip())
            if desc_embedding_in in self._rc.memory.embeddings:
                event_embedding = self._rc.memory.embeddings[desc_embedding_in]
            else:
                event_embedding = get_embedding(desc_embedding_in)
            event_embedding_pair = (desc_embedding_in, event_embedding)

            # Get event poignancy.
            event_poignancy = generate_poig_score(self,
                                                  "action",
                                                  desc_embedding_in)

            # If we observe the persona's self chat, we include that in the memory
            # of the persona here.
            chat_node_ids = []
            if p_event[0] == f"{self.name}" and p_event[1] == "chat with":
                curr_event = self._rc.scratch.act_event
                if self._rc.scratch.act_description in self._rc.memory.embeddings:
                    chat_embedding = self._rc.memory.embeddings[
                        self._rc.scratch.act_description]
                else:
                    chat_embedding = get_embedding(self._rc.scratch
                                                   .act_description)
                chat_embedding_pair = (self._rc.scratch.act_description,
                                       chat_embedding)
                chat_poignancy = generate_poig_score(self._rc.scratch, "chat",
                                                     self._rc.scratch.act_description)
                chat_node = self._rc.memory.add_chat(self._rc.scratch.curr_time, None,
                                                     curr_event[0], curr_event[1], curr_event[2],
                                                     self._rc.scratch.act_description, keywords,
                                                     chat_poignancy, chat_embedding_pair,
                                                     self._rc.scratch.chat)
                chat_node_ids = [chat_node.node_id]

            # Finally, we add the current event to the agent's memory.
            ret_events += [self._rc.memory.add_event(self._rc.scratch.curr_time, None,
                                                     s, p, o, desc, keywords, event_poignancy,
                                                     event_embedding_pair, chat_node_ids)]
            self._rc.scratch.importance_trigger_curr -= event_poignancy
            self._rc.scratch.importance_ele_n += 1

        return ret_events

    async def retrieve(self, focus_points, n=30):
        # TODO retrieve memories from agent_memory
        retrieve_memories = new_agent_retrieve(self,focus_points,n)
        return retrieve_memories

    async def plan(self):
        # TODO make a plan

        # TODO judge if start a conversation

        # TODO update plan

        # TODO re-add result into memory
        pass

    async def reflect(self):
        # TODO reflection if meet reflect condition

        # TODO re-add result to memory
        pass

    def execute(self, plan: str):
        """
        Args:
            plan: This is a string address of the action we need to execute.
            It comes in the form of "{world}:{sector}:{arena}:{game_objects}".
            It is important that you access this without doing negative
            indexing (e.g., [-1]) because the latter address elements may not be
            present in some cases.
            e.g., "dolores double studio:double studio:bedroom 1:bed"
        """
        roles = self._rc.env.get_roles()
        maze = self._rc.env.maze
        if "<random>" in plan and self._rc.scratch.planned_path == []:
            self._rc.scratch.act_path_set = False

        # <act_path_set> is set to True if the path is set for the current action.
        # It is False otherwise, and means we need to construct a new path.
        if not self._rc.scratch.act_path_set:
            # <target_tiles> is a list of tile coordinates where the persona may go
            # to execute the current action. The goal is to pick one of them.
            target_tiles = None
            logger.info("plan: ", plan)

            if "<persona>" in plan:
                # Executing persona-persona interaction.
                target_p_tile = (roles[plan.split("<persona>")[-1].strip()]
                                 .scratch.curr_tile)
                potential_path = path_finder(maze.collision_maze,
                                             self._rc.scratch.curr_tile,
                                             target_p_tile,
                                             collision_block_id)
                if len(potential_path) <= 2:
                    target_tiles = [potential_path[0]]
                else:
                    potential_1 = path_finder(maze.collision_maze,
                                              self._rc.scratch.curr_tile,
                                              potential_path[int(len(potential_path) / 2)],
                                              collision_block_id)
                    potential_2 = path_finder(maze.collision_maze,
                                              self._rc.scratch.curr_tile,
                                              potential_path[int(len(potential_path) / 2) + 1],
                                              collision_block_id)
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
                target_tiles = maze.address_tiles[plan]
                target_tiles = random.sample(list(target_tiles), 1)

            else:
                # This is our default execution. We simply take the persona to the
                # location where the current action is taking place.
                # Retrieve the target addresses. Again, plan is an action address in its
                # string form. <maze.address_tiles> takes this and returns candidate
                # coordinates.
                if plan not in maze.address_tiles:
                    maze.address_tiles["Johnson Park:park:park garden"]  # ERRORRRRRRR
                else:
                    target_tiles = maze.address_tiles[plan]

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
                curr_event_set = maze.access_tile(i)["events"]
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
            curr_tile = self._rc.scratch.curr_tile
            collision_maze = maze.collision_maze
            closest_target_tile = None
            path = None
            for i in target_tiles:
                # path_finder takes a collision_mze and the curr_tile coordinate as
                # an input, and returns a list of coordinate tuples that becomes the
                # path.
                # e.g., [(0, 1), (1, 1), (1, 2), (1, 3), (1, 4)...]
                curr_path = path_finder(maze.collision_maze,
                                        curr_tile,
                                        i,
                                        collision_block_id)
                if not closest_target_tile:
                    closest_target_tile = i
                    path = curr_path
                elif len(curr_path) < len(path):
                    closest_target_tile = i
                    path = curr_path

            # Actually setting the <planned_path> and <act_path_set>. We cut the
            # first element in the planned_path because it includes the curr_tile.
            self._rc.scratch.planned_path = path[1:]
            self._rc.scratch.act_path_set = True

        # Setting up the next immediate step. We stay at our curr_tile if there is
        # no <planned_path> left, but otherwise, we go to the next tile in the path.
        ret = self._rc.scratch.curr_tile
        if self._rc.scratch.planned_path:
            ret = self._rc.scratch.planned_path[0]
            self._rc.scratch.planned_path = self._rc.scratch.planned_path[1:]

        description = f"{self._rc.scratch.act_description}"
        description += f" @ {self._rc.scratch.act_address}"

        execution = ret, self._rc.scratch.act_pronunciatio, description
        return execution

    def update_role_env(self) -> bool:
        role_env = get_role_environment(self.sim_code, self.name, self.step)
        ret = True
        if role_env:
            for key, val in self.game_obj_cleanup.items():
                self._rc.env.maze.turn_event_from_tile_idle(key, val)

            # reset game_obj_cleanup
            self.game_obj_cleanup = dict()
            curr_tile = self.role_tile
            new_tile = (role_env["x"], role_env["y"])
            self._rc.env.maze.remove_subject_events_from_tile(self.name, curr_tile)
            self._rc.env.maze.add_event_from_tile(self.scratch.get_curr_event_and_desc(), new_tile)

            # the persona will travel to get to their destination. *Once*
            # the persona gets there, we activate the object action.
            if not self.scratch.planned_path:
                self.game_obj_cleanup[self.scratch.get_curr_event_and_desc()] = new_tile
                self._rc.env.maze.add_event_from_tile(self.scratch.get_curr_event_and_desc(), new_tile)
                blank = (self.scratch.get_curr_obj_event_and_desc()[0], None, None, None)
                self._rc.env.maze.remove_event_from_tile(blank, new_tile)
        else:
            ret = False
            time.sleep(1)
            logger.warning(f"{self.sim_code}/environment/{self.step}.json not exist or parses failed,"
                           f"sleep 1s and re-check")
        return ret

    async def _react(self) -> Message:
        # update role env
        ret = self.update_role_env()
        if not ret:
            # TODO add message
            return

        # TODO observe
        # get maze_env from self._rc.env, and observe env info

        # TODO retrieve, use self._rc.memory 's retrieve functions

        # TODO plan
        plan = self.plan()

        # TODO reflect

        # TODO execute(feed-back into maze_env)
        next_tile, pronunciatio, description = self.execute(plan)
        role_move = {
            "movement": next_tile,
            "pronunciatio": pronunciatio,
            "description": description,
            "chat": self.scratch.chat
        }
        save_movement(self.name, role_move, step=self.step, sim_code=self.sim_code, curr_time=self.curr_time)

        # step update
        self.step += 1
        self.curr_time += datetime.timedelta(seconds=self.sec_per_step)

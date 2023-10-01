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
from pydantic import Field
from pathlib import Path
from operator import itemgetter

from metagpt.roles.role import Role, RoleContext
from metagpt.schema import Message

from ..memory.agent_memory import AgentMemory, BasicMemory
from ..memory.spatial_memory import MemoryTree
from ..actions.dummy_action import DummyAction
from ..actions.user_requirement import UserRequirement
from ..maze_environment import MazeEnvironment
from ..memory.retrieve import agent_retrieve
from ..memory.scratch import Scratch
from ..utils.utils import get_embedding, generate_poig_score

from ..reflect.st_reflect import agent_reflect


class STRoleContext(RoleContext):
    env: 'MazeEnvironment' = Field(default=None)
    memory: AgentMemory = Field(default=AgentMemory)
    scratch: Scratch = Field(default=Scratch)
    spatial_memory: MemoryTree = Field(default=MemoryTree)


class STRole(Role):
    # 继承Role类，Role类继承RoleContext，这里的逻辑需要认真考虑
    # add a role's property structure to store role's age and so on like GA's Scratch.

    def __init__(self,
                 name: str = "Klaus Mueller",
                 profile: str = "STMember",
                 has_inner_voice: bool = False):

        self._rc = STRoleContext()
        super(STRole, self).__init__(name=name,
                                     profile=profile)

        self._init_actions([])

        if has_inner_voice:
            # TODO add communication action
            self._watch([UserRequirement, DummyAction])
        else:
            self._watch([DummyAction])

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

    async def retrieve(self, query, n = 30 ,topk = 4):
        # TODO retrieve memories from agent_memory
        retrieve_memories = agent_retrieve(self._rc.memory, self._rc.scratch.curr_time, self._rc.scratch.recency_decay, query, n, topk)
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

    async def _react(self) -> Message:
        maze_env = self._rc.env
        # TODO observe
        # get maze_env from self._rc.env, and observe env info

        # TODO retrieve, use self._rc.memory 's retrieve functions

        # TODO plan

        # TODO reflect

        # TODO execute(feed-back into maze_env)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : gen_action_details

import datetime
import random

from metagpt.logs import logger
from metagpt.schema import Message

from ..roles.st_role import STRole
from ..maze import Maze
from .st_action import STAction

    # act_world = maze.access_tile(role.scratch.curr_tile)["world"]
    # act_sector = maze.access_tile(role.scratch.curr_tile)["sector"]
    # act_sector = generate_action_sector(act_desp, role, maze)
    # act_arena = generate_action_arena(act_desp, role, maze, act_world, act_sector)
    # act_address = f"{act_world}:{act_sector}:{act_arena}"
    # act_game_object = generate_action_game_object(act_desp, act_address,
    #                                                 role, maze)
    # new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
    # act_pron = generate_action_pronunciatio(act_desp, role)
    # act_event = generate_action_event_triple(act_desp, role)
    # # Persona's actions also influence the object states. We set those up here. 
    # act_obj_desp = generate_act_obj_desc(act_game_object, act_desp, role)
    # act_obj_pron = generate_action_pronunciatio(act_obj_desp, role)
    # act_obj_event = generate_act_obj_event_triple(act_game_object, 
    #                                                 act_obj_desp, role)
    # Adding the action to role's queue. 
    # role.scratch.add_new_action(new_address, 
    #                                 int(act_dura), 
    #                                 act_desp, 
    #                                 act_pron, 
    #                                 act_event,
    #                                 None,
    #                                 None,
    #                                 None,
    #                                 None,
    #                                 act_obj_desp, 
    #                                 act_obj_pron, 
    #                                 act_obj_event)
    
class GenActionSector(STAction):

    def __init__(self, name="GenActionSector", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cleaned_response = llm_resp.split("}")[0]
        return cleaned_response  

    def _func_validate(self, llm_resp: str, prompt: str):
        if len(llm_resp.strip()) < 1: 
            return False
        if "}" not in llm_resp:
            return False
        if "," in llm_resp: 
            return False
        return True       

    def _func_fail_default_resp(self):
        fs = ("kitchen")
        return fs   

    def run(self, role: STRole, maze: Maze, act_desp: str):
        def create_prompt_input(role, maze, act_desp): 
            act_world = f"{maze.access_tile(role.scratch.curr_tile)['world']}"
            
            prompt_input = []
            
            prompt_input += [role.scratch.get_str_name()]
            prompt_input += [role.scratch.living_area.split(":")[1]]
            x = f"{act_world}:{role.scratch.living_area.split(':')[1]}"
            prompt_input += [role.s_mem.get_str_accessible_sector_arenas(x)]


            prompt_input += [role.scratch.get_str_name()]
            prompt_input += [f"{maze.access_tile(role.scratch.curr_tile)['sector']}"]
            x = f"{act_world}:{maze.access_tile(role.scratch.curr_tile)['sector']}"
            prompt_input += [role.s_mem.get_str_accessible_sector_arenas(x)]

            if role.scratch.get_str_daily_plan_req() != "": 
                prompt_input += [f"\n{role.scratch.get_str_daily_plan_req()}"]
            else: 
                prompt_input += [""]


            # MAR 11 TEMP
            prompt_input = []
            act_world = maze.access_tile(role.scratch.curr_tile)["world"]
            accessible_sector_str = role.s_mem.get_str_accessible_sectors(act_world)
            curr = accessible_sector_str.split(", ")
            fin_accessible_sectors = []
            for i in curr: 
                if "'s house" in i: 
                    if role.scratch.last_name in i: 
                        fin_accessible_sectors += [i]
            else: 
                fin_accessible_sectors += [i]
            accessible_sector_str = ", ".join(fin_accessible_sectors)
            # END MAR 11 TEMP

            prompt_input += [accessible_sector_str]

            act_desp_1 = act_desp
            act_desp_2 = act_desp
            if "(" in act_desp: 
                act_desp_1 = act_desp.split("(")[0].strip()
                act_desp_2 = act_desp.split("(")[-1][:-1]
            prompt_input += [role.scratch.get_str_name()]
            prompt_input += [act_desp_1]

            prompt_input += [act_desp_2]
            prompt_input += [role.scratch.get_str_name()]
            return prompt_input
        
        prompt_template = "action_location_sector_v1.txt"
        prompt_input = create_prompt_input(role, maze, act_desp)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)

        self.fail_default_resp = self._func_fail_default_resp()
        output = self._run_v1(prompt)
        y = f"{maze.access_tile(role.scratch.curr_tile)['world']}"
        x = [i.strip() for i in role.s_mem.get_str_accessible_sectors(y).split(",")]
        if output not in x: 
            # output = random.choice(x)
            output = role.scratch.living_area.split(":")[1]
        return output


class GenActionArena(STAction):
    def __init__(self, name="GenActionArena", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cleaned_response = llm_resp.split("}")[0]
        return cleaned_response

    def _func_validate(self, llm_resp: str, prompt: str): 
        if len(llm_resp.strip()) < 1: 
            return False
        if "}" not in llm_resp:
            return False
        if "," in llm_resp: 
            return False
        return True
    
    def _func_fail_default_resp(self):
        fs = ("kitchen")
        return fs
    
    def run(self, role: STRole, maze: Maze, act_desp: str, act_world: str, act_sector: str):
        def create_prompt_input(role, maze, act_desp, act_world, act_sector): 
            prompt_input = []
            # prompt_input += [role.scratch.get_str_name()]
            # prompt_input += [maze.access_tile(role.scratch.curr_tile)["arena"]]
            # prompt_input += [maze.access_tile(role.scratch.curr_tile)["sector"]]
            prompt_input += [role.scratch.get_str_name()]
            x = f"{act_world}:{act_sector}"
            prompt_input += [act_sector]

            # MAR 11 TEMP
            accessible_arena_str = role.s_mem.get_str_accessible_sector_arenas(x)
            curr = accessible_arena_str.split(", ")
            fin_accessible_arenas = []
            for i in curr: 
                if "'s room" in i: 
                    if role.scratch.last_name in i: 
                        fin_accessible_arenas += [i]
                else: 
                    fin_accessible_arenas += [i]
            accessible_arena_str = ", ".join(fin_accessible_arenas)
            # END MAR 11 TEMP
            prompt_input += [accessible_arena_str]
            act_desp_1 = act_desp
            act_desp_2 = act_desp
            if "(" in act_desp: 
                act_desp_1 = act_desp.split("(")[0].strip()
                act_desp_2 = act_desp.split("(")[-1][:-1]
            prompt_input += [role.scratch.get_str_name()]
            prompt_input += [act_desp_1]

            prompt_input += [act_desp_2]
            prompt_input += [role.scratch.get_str_name()]

            prompt_input += [act_sector]
            prompt_input += [accessible_arena_str]
            return prompt_input

        prompt_template = "action_location_object_vMar11.txt"
        prompt_input = create_prompt_input(role, maze, act_desp, act_world, act_sector)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp()
        output = self._run_v1(prompt) 
        return output


class GenActionObject(STAction):
    def __init__(self, name="GenActionObject", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)   

    def _func_validate(self, llm_resp: str, prompt: str): 
        if len(llm_resp.strip()) < 1: 
            return False
        return True

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cleaned_response = llm_resp.strip()
        return cleaned_response

    def _func_fail_default_resp(self):
        fs = ("bed")
        return fs

    def run(self, role: STRole, act_desp: str, temp_address: str):

        def create_prompt_input(role, act_desp, temp_address): 
            prompt_input = []
            if "(" in act_desp: 
                act_desp = act_desp.split("(")[-1][:-1]
            
            prompt_input += [act_desp]
            prompt_input += [role
                            .s_mem.get_str_accessible_arena_game_objects(temp_address)]
            return prompt_input
        
        prompt_template = "action_object_v2.txt"
        prompt_input = create_prompt_input(role, act_desp, temp_address)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp()
        output = self._run_v1(prompt) 
        x = [i.strip() for i in role.s_mem.get_str_accessible_arena_game_objects(temp_address).split(",")]
        if output not in x: 
            output = random.choice(x)
        return output


class GenPronunciatio(STAction):
    def __init__(self, name="GenPronunciatio", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm) 

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cr = llm_resp.strip()
        if len(cr) > 3:
            cr = cr[:3]
        return cr

    def _func_validate(self, llm_resp: str, prompt: str): 
        try: 
            self._func_cleanup(llm_resp, prompt="")
            if len(llm_resp) == 0: 
                return False
        except: 
           return False
        return True 

    def _func_fail_default_resp(self):
        fs = "😋"
        return fs

    def run(self, role: STRole, act_desp: str)
        def create_prompt_input(act_desp): 
            if "(" in act_desp: 
                act_desp = act_desp.split("(")[-1].split(")")[0]
            prompt_input = [act_desp]
            return prompt_input
  

        prompt_template = "generate_pronunciatio_v1.txt" 
        prompt_input = create_prompt_input(act_desp)  
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        example_output = "🛁🧖‍♀️" 
        special_instruction = "The value for the output must ONLY contain the emojis." 
        self.fail_default_resp = self._func_fail_default_resp()
        output = self._run_v2(prompt, example_output, special_instruction)
        return output


class GenEventTriple(STAction):
    def __init__(self, name="GenEventTriple", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm) 

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cr = llm_resp.strip()
        cr = [i.strip() for i in cr.split(")")[0].split(",")]
        return cr

    def _func_validate(self, llm_resp: str, prompt: str): 
        try: 
            llm_resp = self._func_cleanup(llm_resp, prompt="")
            if len(llm_resp) != 2: 
                return False
        except: 
           return False
        return True 

    def _func_fail_default_resp(self, role): 
        fs = (role.name, "is", "idle")
        return fs        

    def run(self, role: STRole, act_desp: str):
        def create_prompt_input(role, act_desp): 
            if "(" in act_desp: 
                act_desp = act_desp.split("(")[-1].split(")")[0]
            prompt_input = [role.name, 
                            act_desp,
                            role.name]
            return prompt_input
  
        prompt_template = "generate_event_triple_v1.txt"
        prompt_input = create_prompt_input(role, act_desp)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp(role)
        output = self._run_v1(prompt)
        output = (role.name, output[0], output[1])
        return output


class GenActObjDescription(STAction):
    def __init__(self, name="GenActObjDescription", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm) 

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cr = llm_resp.strip()
        if cr[-1] == ".": cr = cr[:-1]
        return cr

    def _func_validate(self, llm_resp: str, prompt: str): 
        try: 
            llm_resp = self._func_cleanup(llm_resp, prompt="")
        except: 
            return False
        return True 

    def _func_fail_default_resp(self,act_game_object): 
        fs = f"{act_game_object} is idle"
        return fs
        
    def run(self, role: STRole, act_game_object: str, act_desp: str): 
        def create_prompt_input(act_game_object, act_desp, role): 
            prompt_input = [act_game_object, 
                            role.name,
                            act_desp,
                            act_game_object,
                            act_game_object]
            return prompt_input
  
        prompt_template = "generate_obj_event_v1.txt" ########
        prompt_input = create_prompt_input(act_game_object, act_desp, role)  ########
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        example_output = "being fixed" ########
        special_instruction = "The output should ONLY contain the phrase that should go in <fill in>." ########
        self.fail_default_resp = self._func_fail_default_resp(act_game_object) ########
        output = self._run_v2(prompt, example_output, special_instruction)
        return output
  

class GenObjEventTriple(STAction):
    def __init__(self, name="GenObjEventTriple", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm) 

    def _func_cleanup(self, llm_resp: str, prompt: str):
        cr = llm_resp.strip()
        cr = [i.strip() for i in cr.split(")")[0].split(",")]
        return cr

    def _func_validate(self, llm_resp: str, prompt: str): 
        try: 
            llm_resp = self._func_cleanup(llm_resp, prompt="")
            if len(llm_resp) != 2: 
                return False
        except: return False
        return True 

    def _func_fail_default_resp(self,act_game_object): 
        fs = (act_game_object, "is", "idle")
        return fs

    def run(self, role: STRole, act_game_object, act_obj_desc):
        def create_prompt_input(act_game_object, act_obj_desc): 
            prompt_input = [act_game_object, 
                            act_obj_desc,
                            act_game_object]
            return prompt_input
  
        prompt_template = "generate_event_triple_v1.txt"
        prompt_input = create_prompt_input(act_game_object, act_obj_desc)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp(role)
        output = self._run_v1(prompt)
        output = (role.name, output[0], output[1])
        return output
    

class GenActionDetails(STAction):
    def __init__(self, name="GenActionDetails", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm) 

    def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        pass

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        # TODO -- this sometimes generates error 
        try: 
            self._func_cleanup(llm_resp)
        except: 
            return False
        return True

    def run(self,
            role: STRole,
            act_desp: str,
            act_dura):
        maze = role._rc.env.maze
        act_world = maze.access_tile(role.scratch.curr_tile)["world"]
        act_sector = GenActionSector().run(role, maze, act_desp)
        act_arena = GenActionArena().run(role, maze, act_desp, act_world, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_arena}"
        act_game_object = GenActionObject().run(role, act_desp, act_address)
        new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
        act_pron = GenPronunciatio().run(role, act_desp)
        act_event = GenEventTriple().run(role, act_desp)
        # Persona's actions also influence the object states. We set those up here. 
        act_obj_desp = GenActObjDescription().run(role, act_game_object, act_desp)
        act_obj_pron = GenPronunciatio().run(role, act_obj_desp)
        act_obj_event = GenObjEventTriple().run(role, act_game_object, 
                                                        act_obj_desp)
        result_dict = {
            "action_address": new_address,
            "action_duration": int(act_dura),
            "act_desp": act_desp,
            "action_pronunciatio": act_pron,
            "action_event": act_event,
            "chatting_with": None,
            "chat": None,
            "chatting_with_buffer": None,
            "chatting_end_time": None,
            "act_obj_description": act_obj_desp,
            "act_obj_pronunciatio": act_obj_pron,
            "act_obj_event": act_obj_event}
        return result_dict

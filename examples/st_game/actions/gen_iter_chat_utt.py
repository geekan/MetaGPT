#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : generate_iterative_chat_utt

from metagpt.logs import logger
from metagpt.schema import Message

from ..roles.st_role import STRole
from ..actions.st_action import STAction
from ..utils.utils import extract_first_json_dict
from ..maze import Maze


class GenIterChatUTT(STAction):

    def __init__(self, name="GenIterChatUTT", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        resp = False
        try:
            _ = extract_first_json_dict(llm_resp)
            resp = True
        except Exception as exp:
            pass
        return resp

    def _func_cleanup(self, llm_resp: str, prompt: str) -> dict:
        gpt_response = extract_first_json_dict(llm_resp)

        cleaned_dict = dict()
        cleaned = []
        for key, val in gpt_response.items():
            cleaned += [val]
        cleaned_dict["utterance"] = cleaned[0]
        cleaned_dict["end"] = True
        if "f" in str(cleaned[1]) or "F" in str(cleaned[1]):
            cleaned_dict["end"] = False

        return cleaned_dict

    def _func_fail_default_resp(self) -> dict:
        cleaned_dict = dict()
        cleaned_dict["utterance"] = "..."
        cleaned_dict["end"] = False
        return cleaned_dict

    def run(self, maze: Maze, init_role: STRole, target_role: STRole, retrieved: dict, curr_context: str,
            curr_chat: list[str], *args, **kwargs) -> dict:
        def create_prompt_input(maze: Maze, init_role: STRole, target_role: STRole,
                                retrieved: dict, curr_context: str, curr_chat: list[str]):
            role = init_role
            scratch = role._rc.scratch
            target_scratch = target_role._rc.scratch
            prev_convo_insert = "\n"
            if role._rc.memory.chat_list:
                for i in role._rc.memory.chat_list:
                    if i.object == target_role.name:
                        v1 = int((scratch.curr_time - i.created).total_seconds() / 60)
                        prev_convo_insert += f"{str(v1)} minutes ago, {scratch.name} and " \
                                             f"{target_scratch.name} were already {i.description} " \
                                             f"This context takes place after that conversation."
                        break
            if prev_convo_insert == "\n":
                prev_convo_insert = ""
            if role._rc.memory.chat_list:
                if int((scratch.curr_time - role._rc.memory.chat_list[-1].created).total_seconds() / 60) > 480:
                    prev_convo_insert = ""
            print(prev_convo_insert)

            curr_sector = f"{maze.access_tile(scratch.curr_tile)['sector']}"
            curr_arena = f"{maze.access_tile(scratch.curr_tile)['arena']}"
            curr_location = f"{curr_arena} in {curr_sector}"

            retrieved_str = ""
            for key, vals in retrieved.items():
                for v in vals:
                    retrieved_str += f"- {v.description}\n"

            convo_str = ""
            for i in curr_chat:
                convo_str += ": ".join(i) + "\n"
            if convo_str == "":
                convo_str = "[The conversation has not started yet -- start it!]"

            init_iss = f"Here is Here is a brief description of {scratch.name}.\n{scratch.get_str_iss()}"
            prompt_input = [init_iss, scratch.name, retrieved_str, prev_convo_insert,
                            curr_location, curr_context, scratch.name, target_scratch.name,
                            convo_str, scratch.name, target_scratch.name,
                            scratch.name, scratch.name,
                            scratch.name
                            ]
            return prompt_input

        prompt_input = create_prompt_input(maze, init_role, target_role, retrieved, curr_context, curr_chat)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "iterative_convo_v1.txt")
        # original using `ChatGPT_safe_generate_response_OLD`
        self.fail_default_resp = self._func_fail_default_resp()
        output = self._run_v1(prompt)
        return output

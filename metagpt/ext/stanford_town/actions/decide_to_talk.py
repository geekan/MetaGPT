#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : device to talk to another role, return yes or no

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class DecideToTalk(STAction):
    name: str = "DecideToTalk"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        resp = False
        try:
            if llm_resp.split("Answer in yes or no:")[-1].strip().lower() in ["yes", "no"]:
                resp = True
        except ValueError:
            pass
        return resp

    def _func_cleanup(self, llm_resp: str, prompt: str) -> str:
        return llm_resp.split("Answer in yes or no:")[-1].strip().lower()

    def _func_fail_default_resp(self) -> str:
        return "yes"

    async def run(self, init_role: "STRole", target_role: "STRole", retrieved: dict, *args, **kwargs) -> bool:
        """Run action"""

        def create_prompt_input(init_role: "STRole", target_role: "STRole", retrieved: dict) -> str:
            scratch = init_role.rc.scratch
            target_scratch = target_role.rc.scratch
            last_chat = init_role.rc.memory.get_last_chat(target_role.name)
            last_chatted_time = ""
            last_chat_about = ""
            if last_chat:
                last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
                last_chat_about = last_chat.description

            context = ""
            for c_node in retrieved["events"]:
                curr_desc = c_node.description.split(" ")
                curr_desc[2:3] = ["was"]
                curr_desc = " ".join(curr_desc)
                context += f"{curr_desc}. "
            context += "\n"
            for c_node in retrieved["thoughts"]:
                context += f"{c_node.description}. "

            curr_time = scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
            init_act_desc = scratch.act_description
            if "(" in init_act_desc:
                init_act_desc = init_act_desc.split("(")[-1][:-1]

            if len(scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                init_p_desc = f"{init_role.name} is already {init_act_desc}"
            elif "waiting" in init_act_desc:
                init_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                init_p_desc = f"{init_role.name} is on the way to {init_act_desc}"

            target_act_desc = scratch.act_description
            if "(" in target_act_desc:
                target_act_desc = target_act_desc.split("(")[-1][:-1]

            if len(target_scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                target_p_desc = f"{target_role.name} is already {target_act_desc}"
            elif "waiting" in init_act_desc:
                target_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                target_p_desc = f"{target_role.name} is on the way to {target_act_desc}"

            prompt_input = []
            prompt_input += [context]

            prompt_input += [curr_time]

            prompt_input += [init_role.name]
            prompt_input += [target_role.name]
            prompt_input += [last_chatted_time]
            prompt_input += [last_chat_about]

            prompt_input += [init_p_desc]
            prompt_input += [target_p_desc]
            prompt_input += [init_role.name]
            prompt_input += [target_role.name]
            return prompt_input

        prompt_input = create_prompt_input(init_role, target_role, retrieved)
        prompt = self.generate_prompt_with_tmpl_filename(
            prompt_input=prompt_input, tmpl_filename="decide_to_talk_v2.txt"
        )
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=20)  # yes or no
        result = True if output == "yes" else False
        logger.info(f"Role: {init_role.name} Action: {self.cls_name} output: {result}")
        return result

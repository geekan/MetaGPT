#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : gen_daily_schedule


from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class GenDailySchedule(STAction):
    name: str = "GenDailySchedule"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt="")
        except Exception:
            return False
        return True

    def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        cr = []
        _cr = llm_resp.split(")")
        for i in _cr:
            if i[-1].isdigit():
                i = i[:-1].strip()
                if i[-1] == "." or i[-1] == ",":
                    cr += [i[:-1].strip()]
        return cr

    def _func_fail_default_resp(self) -> int:
        fs = [
            "wake up and complete the morning routine at 6:00 am",
            "eat breakfast at 7:00 am",
            "read a book from 8:00 am to 12:00 pm",
            "have lunch at 12:00 pm",
            "take a nap from 1:00 pm to 4:00 pm",
            "relax and watch TV from 7:00 pm to 8:00 pm",
            "go to bed at 11:00 pm",
        ]
        return fs

    async def run(self, role: "STRole", wake_up_hour: str):
        def create_prompt_input(role, wake_up_hour):
            prompt_input = []
            prompt_input += [role.scratch.get_str_iss()]
            prompt_input += [role.scratch.get_str_lifestyle()]
            prompt_input += [role.scratch.get_str_curr_date_str()]
            prompt_input += [role.scratch.get_str_firstname()]
            prompt_input += [f"{str(wake_up_hour)}:00 am"]
            return prompt_input

        wake_up_hour = int(wake_up_hour)
        prompt_template = "daily_planning_v6.txt"
        prompt_input = create_prompt_input(role, wake_up_hour)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=500)
        output = [f"wake up and complete the morning routine at {wake_up_hour}:00 am"] + output
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {output}")
        return output

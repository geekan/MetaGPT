#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : wake_up


from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class WakeUp(STAction):
    name: str = "WakeUp"

    def _func_validate(self, llm_resp: str, prompt: str = None) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt="")
        except Exception:
            return False
        return True

    def _func_cleanup(self, llm_resp: str, prompt: str) -> int:
        cr = int(llm_resp.strip().lower().split("am")[0])
        return cr

    def _func_fail_default_resp(self) -> int:
        fs = 8
        return fs

    async def run(self, role: "STRole"):
        def create_prompt_input(role):
            prompt_input = [
                role.scratch.get_str_iss(),
                role.scratch.get_str_lifestyle(),
                role.scratch.get_str_firstname(),
            ]
            return prompt_input

        prompt_input = create_prompt_input(role)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "wake_up_hour_v1.txt")
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=5)
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {output}")
        return output

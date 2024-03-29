#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class AgentWhisperThoughtAction(STAction):
    name: str = "AgentWhisperThoughtAction"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except Exception:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> list:
        return llm_resp.split('"')[0].strip()

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: "STRole", statements: str, test_input=None, verbose=False) -> str:
        def create_prompt_input(role: "STRole", statements, test_input=None):
            prompt_input = [role.scratch.name, statements]
            return prompt_input

        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "whisper_inner_thought_v1.txt")

        output = await self._run_gpt35_max_tokens(prompt, max_tokens=50)
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {output}")
        return output

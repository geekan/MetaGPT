#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : summarize relationship in a agent chat

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class AgentChatSumRel(STAction):
    name: str = "AgentChatSumRel"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        resp = False
        try:
            _ = llm_resp.split('"')[0].strip()
            resp = True
        except Exception:
            pass
        return resp

    def _func_cleanup(self, llm_resp: str, prompt: str) -> str:
        return llm_resp.split('"')[0].strip()

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, init_role: "STRole", target_role: "STRole", statements: str) -> str:
        def create_prompt_input(init_role: "STRole", target_role: "STRole", statements: str) -> str:
            prompt_input = [statements, init_role.name, target_role.name]
            return prompt_input

        prompt_input = create_prompt_input(init_role, target_role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "summarize_chat_relationship_v2.txt")

        example_output = "Jane Doe is working on a project"
        special_instruction = "The output should be a string that responds to the question."
        output = await self._run_gpt35(prompt, example_output, special_instruction)
        logger.info(f"Role: {init_role.name} Action: {self.cls_name} output: {output}")
        return output

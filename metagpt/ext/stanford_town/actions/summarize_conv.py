#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : summarize the content of agents' conversation

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class SummarizeConv(STAction):
    name: str = "SummarizeConv"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        resp = False
        try:
            _ = self._func_cleanup(llm_resp, prompt)
            resp = True
        except Exception:
            pass
        return resp

    def _func_cleanup(self, llm_resp: str, prompt: str) -> str:
        ret = "conversing about " + llm_resp.strip()
        return ret

    def _func_fail_default_resp(self) -> str:
        return "conversing with a housemate about morning greetings"

    async def run(self, conv: list):
        def create_prompt_input(conversation: list):
            convo_str = ""
            for row in conversation:
                convo_str += f'{row[0]}: "{row[1]}"\n'
            prompt_input = [convo_str]
            return prompt_input

        prompt_input = create_prompt_input(conv)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "summarize_conversation_v1.txt")

        example_output = "conversing about what to eat for lunch"
        special_instruction = (
            "The output must continue the sentence above by filling in the <fill in> tag. "
            "Don't start with 'this is a conversation about...' Just finish the sentence "
            "but do not miss any important details (including who are chatting)."
        )
        output = await self._run_gpt35(prompt, example_output, special_instruction)
        logger.info(f"Action: {self.cls_name} output: {output}")
        return output

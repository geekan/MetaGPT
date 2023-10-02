#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown Action

from typing import Union, Optional
from abc import abstractmethod
import json

from metagpt.actions.action import Action
from metagpt.schema import Message

from ..utils.const import PROMPTS_DIR


class STAction(Action):

    def __init__(self, name="STAction", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)
        self.prompt_dir = PROMPTS_DIR
        self.fail_default_resp = None

    @abstractmethod
    def _func_validate(self, llm_resp: str, prompt: str):
        raise NotImplementedError

    @abstractmethod
    def _func_cleanup(self, llm_resp: str, prompt: str):
        raise NotImplementedError

    @abstractmethod
    def _func_fail_default_resp(self):
        raise NotImplementedError

    def generate_prompt_with_tmpl_filename(self, prompt_input: Union[str, list], tmpl_filename) -> str:
        """
        same with `generate_prompt`
        Args:
            prompt_input: the input we want to feed in (IF THERE ARE MORE THAN ONE INPUT, THIS CAN BE A LIST.)
            tmpl_filename: prompt template filename
        Returns:
            a str prompt that will be sent to LLM server.
        """
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        f = open(str(self.prompt_dir.joinpath(tmpl_filename)), "r")
        prompt = f.read()
        f.close()
        for count, i in enumerate(prompt_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        if "<commentblockmarker>###</commentblockmarker>" in prompt:
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
        return prompt.strip()

    def _ask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        return self.llm.ask(prompt)

    def _run_v1(self, prompt: str, retry: int = 3) -> str:
        """
            same with `gpt_structure.safe_generate_response`
            default post-preprocess operations of LLM response
        """
        for idx in range(retry):
            llm_resp = self._ask(prompt)
            if self._func_validate(llm_resp, prompt):
                return self._func_cleanup(llm_resp, prompt)
        return self.fail_default_resp

    def _run_v2(self,
                prompt: str,
                example_output: str,
                special_instruction: str,
                retry: int = 3):
        """ same with `gpt_structure.ChatGPT_safe_generate_response` """
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
        prompt += "Example output json:\n"
        prompt += '{"output": "' + str(example_output) + '"}'

        for idx in range(retry):
            try:
                llm_resp = self._ask(prompt)
                print("llm_resp ", llm_resp)
                end_idx = llm_resp.strip().rfind("}") + 1
                llm_resp = llm_resp[:end_idx]
                llm_resp = json.loads(llm_resp)["output"]

                if self._func_validate(llm_resp, prompt):
                    return self._func_cleanup(llm_resp, prompt)
            except Exception as exp:
                pass
        return False

    def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")

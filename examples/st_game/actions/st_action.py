#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown Action
import time
from typing import Union, Optional, Any
from abc import abstractmethod
import json

from metagpt.actions.action import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.config import CONFIG

from examples.st_game.utils.const import PROMPTS_DIR


class STAction(Action):

    def __init__(self, name="STAction", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)
        self.prompt_dir = PROMPTS_DIR
        self.fail_default_resp = None

    @property
    def cls_name(self):
        return self.__class__.__name__

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

    def _ask(self, prompt: str) -> str:
        return self.llm.ask(prompt)

    def _ask_nonchat(self, prompt: str) -> str:
        return self.llm.ask_nonchat(prompt)

    def _run_text_davinci(self, prompt: str, model_name: str = "gpt-3.5-turbo-instruct",
                          max_tokens: int = 50, retry: int = 3):
        """
            same with `gpt_structure.safe_generate_response`
            default post-preprocess operations of LLM response
        """
        assert model_name in ["gpt-3.5-turbo-instruct", "text-davinci-002", "text-davinci-003"]
        for idx in range(retry):
            tmp_model_name = self.llm.model
            tmp_max_tokens_rsp = CONFIG.max_tokens_rsp
            CONFIG.max_tokens_rsp = max_tokens
            self.llm.model = model_name

            llm_resp = self._ask_nonchat(prompt)

            CONFIG.max_tokens_rsp = tmp_max_tokens_rsp
            self.llm.model = tmp_model_name
            logger.info(f"Action: {self.cls_name} llm _run_text_davinci raw resp: {llm_resp}")
            if self._func_validate(llm_resp, prompt):
                return self._func_cleanup(llm_resp, prompt)
        return self.fail_default_resp

    def _run_gpt35(self,
                   prompt: str,
                   example_output: str,
                   special_instruction: str,
                   retry: int = 3) -> Union[bool, Any]:
        """ same with `gpt_structure.ChatGPT_safe_generate_response` """
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
        prompt += "Example output json:\n"
        prompt += '{"output": "' + str(example_output) + '"}'

        for idx in range(retry):
            try:
                llm_resp = self._ask(prompt)
                logger.info(f"Action: {self.cls_name} llm _run_gpt35 raw resp: {llm_resp}")
                end_idx = llm_resp.strip().rfind("}") + 1
                llm_resp = llm_resp[:end_idx]
                llm_resp = json.loads(llm_resp)["output"]

                if self._func_validate(llm_resp, prompt):
                    return self._func_cleanup(llm_resp, prompt)
            except Exception as exp:
                logger.warning(f"Action: {self.cls_name} _run_gpt35 exp: {exp}")
                time.sleep(5)  # usually avoid `Rate limit`
        return False

    def _run_gpt35_wo_extra_prompt(self,
                                   prompt: str,
                                   retry: int = 3) -> str:
        for idx in range(retry):
            try:
                llm_resp = self._ask(prompt).strip()
                logger.info(f"Action: {self.cls_name} llm _run_gpt35_wo_extra_prompt raw resp: {llm_resp}")
                if self._func_validate(llm_resp, prompt):
                    return self._func_cleanup(llm_resp, prompt)
            except Exception as exp:
                logger.warning(f"Action: {self.cls_name} _run_gpt35_wo_extra_prompt exp: {exp}")
                time.sleep(5)  # usually avoid `Rate limit`
        return self.fail_default_resp

    def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")

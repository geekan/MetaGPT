#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown Action
import json
import time
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.ext.stanford_town.utils.const import PROMPTS_DIR
from metagpt.logs import logger


class STAction(Action):
    name: str = "STAction"
    prompt_dir: Path = PROMPTS_DIR
    fail_default_resp: Optional[str] = None

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

    async def _aask(self, prompt: str) -> str:
        return await self.llm.aask(prompt)

    async def _run_gpt35_max_tokens(self, prompt: str, max_tokens: int = 50, retry: int = 3):
        for idx in range(retry):
            try:
                tmp_max_tokens_rsp = getattr(config.llm, "max_token", 1500)
                setattr(config.llm, "max_token", max_tokens)
                self.llm.use_system_prompt = False  # to make it behave like a non-chat completions

                llm_resp = await self._aask(prompt)

                setattr(config.llm, "max_token", tmp_max_tokens_rsp)
                logger.info(f"Action: {self.cls_name} llm _run_gpt35_max_tokens raw resp: {llm_resp}")
                if self._func_validate(llm_resp, prompt):
                    return self._func_cleanup(llm_resp, prompt)
            except Exception as exp:
                logger.warning(f"Action: {self.cls_name} _run_gpt35_max_tokens exp: {exp}")
                time.sleep(5)
        return self.fail_default_resp

    async def _run_gpt35(
        self, prompt: str, example_output: str, special_instruction: str, retry: int = 3
    ) -> Union[bool, Any]:
        """same with `gpt_structure.ChatGPT_safe_generate_response`"""
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
        prompt += "Example output json:\n"
        prompt += '{"output": "' + str(example_output) + '"}'

        for idx in range(retry):
            try:
                llm_resp = await self._aask(prompt)
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

    async def _run_gpt35_wo_extra_prompt(self, prompt: str, retry: int = 3) -> str:
        for idx in range(retry):
            try:
                llm_resp = await self._aask(prompt)
                llm_resp = llm_resp.strip()
                logger.info(f"Action: {self.cls_name} llm _run_gpt35_wo_extra_prompt raw resp: {llm_resp}")
                if self._func_validate(llm_resp, prompt):
                    return self._func_cleanup(llm_resp, prompt)
            except Exception as exp:
                logger.warning(f"Action: {self.cls_name} _run_gpt35_wo_extra_prompt exp: {exp}")
                time.sleep(5)  # usually avoid `Rate limit`
        return self.fail_default_resp

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")

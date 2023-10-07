#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Integration Reflect Action

import re

from metagpt.logs import logger

from examples.st_game.actions.st_action import STAction
from examples.st_game.memory.agent_memory import BasicMemory


# Run GPT Prompt Focal Point method
class AgentFocusPt(STAction):

    def __init__(self, name="AgentFocusPt", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        try:
            """
            Cleanup handling has been completed for run_v2
            """
            return llm_resp
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, n: int, test_input=None) -> str:
        def create_prompt_input(role: "STRole", statements, n, test_input=None):
            prompt_input = [statements, str(n)]
            return prompt_input

        prompt_input = create_prompt_input(role, statements, n)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "generate_focal_pt_v1.txt")

        example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
        special_instruction = "Output must be a list of str."
        output = self._run_v2(prompt,
                              example_output,
                              special_instruction)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")
        return output


# Run GPT Prompt Insight and Guidance
class AgentInsightAndGuidance(STAction):

    def __init__(self, name="AgentInsightAndGuidance", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> dict:
        try:
            llm_resp = "1. " + llm_resp.strip()
            ret = dict()
            for i in llm_resp.split("\n"):
                row = i.split(". ")[-1]
                thought = row.split("(because of ")[0].strip()
                evi_raw = row.split("(because of ")[1].split(")")[0].strip()
                evi_raw = re.findall(r'\d+', evi_raw)
                evi_raw = [int(i.strip()) for i in evi_raw]
                ret[thought] = evi_raw
            return ret
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, n: int, test_input=None) -> dict:
        def create_prompt_input(role, statements, n, test_input=None):
            prompt_input = [statements, str(n)]
            return prompt_input

        prompt_input = create_prompt_input(role, statements, n)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "insight_and_evidence_v1.txt")

        output = self._run_v1(prompt)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")
        return output


# Run GPT Prompt Event Triple
class AgentEventTriple(STAction):
    def __init__(self, name="AgentEventTriple", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            llm_resp = self._func_cleanup(llm_resp, prompt="")
            if len(llm_resp) != 2:
                return False
        except:
            return False
        return True

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> list:
        try:
            cr = llm_resp.strip()
            cr = [i.strip() for i in cr.split(")")[0].split(",")]
            if len(cr) != 2:
                return cr[-2:]
            return cr
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, statements: str, role: "STRole", verbose=False) -> tuple:
        def create_prompt_input(statements, role):
            if "(" in statements:
                statements = statements.split("(")[-1].split(")")[0]
            prompt_input = [role.scratch.name,
                            statements,
                            role.scratch.name]
            return prompt_input

        prompt_input = create_prompt_input(statements, role)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "generate_event_triple_v1.txt")

        output = self._run_v1(prompt)
        output = (role.scratch.name, output[0], output[1])
        logger.info(f"Role: {role.name} Run action: {self.__class__.__name__} with result: {output}")

        return output


# Run GPT Prompt Event Poignancy
class AgentEventPoignancy(STAction):
    def __init__(self, name="AgentEventPoignancy", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> int:
        try:
            llm_resp = int(llm_resp.strip())
            return llm_resp
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, test_input=None, verbose=False) -> str:
        def create_prompt_input(role: "STRole", statements: str, test_input=None):
            prompt_input = [role.scratch.name,
                            role.scratch.get_str_iss(),
                            role.scratch.name,
                            statements]
            return prompt_input

        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "poignancy_event_v1.txt")

        example_output = "5"  # ########
        special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
        output = self._run_v2(prompt,
                              example_output,
                              special_instruction)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")

        return output


# Run GPT Prompt Chat Poignancy
class AgentChatPoignancy(STAction):
    def __init__(self, name="AgentChatPoignancy", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> int:
        try:
            llm_resp = int(llm_resp.strip())
            return llm_resp
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, test_input=None, verbose=False) -> str:
        def create_prompt_input(role: "STRole", statements, test_input=None):
            prompt_input = [role.scratch.name,
                            role.scratch.get_str_iss(),
                            role.scratch.name,
                            statements]
            return prompt_input

        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "poignancy_chat_v1.txt")

        example_output = "5"  # ########
        special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
        output = self._run_v2(prompt,
                              example_output,
                              special_instruction)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")

        return output


# Run GPT Prompt Planning Thought on Convo
class AgentPlanThoughtOnConvo(STAction):
    def __init__(self, name="AgentPlanThoughtOnConvo", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        try:
            return llm_resp.split('"')[0].strip()
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, test_input=None, verbose=False) -> str:
        def create_prompt_input(role, statements, test_input=None):
            prompt_input = [statements,
                            role.scratch.name,
                            role.scratch.name,
                            role.scratch.name]
            return prompt_input

        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "planning_thought_on_convo_v1.txt")

        output = self._run_v1(prompt)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")

        return output


# Run GPT Prompt Memory on Convo
class AgentMemoryOnConvo(STAction):
    def __init__(self, name="AgentMemoryOnConvo", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        try:
            return llm_resp.split('"')[0].strip()
        except Exception as exp:
            logger.error(f"{self.__class__.__name__} with error {exp}")

    def _func_fail_default_resp(self) -> str:
        pass

    def run(self, role: "STRole", statements: str, test_input=None, verbose=False) -> str:
        def create_prompt_input(role, statements, test_input=None):
            prompt_input = [statements,
                            role.scratch.name,
                            role.scratch.name,
                            role.scratch.name]
            return prompt_input

        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "memo_on_convo_v1.txt")
        example_output = 'Jane Doe was interesting to talk to.'
        special_instruction = 'The output should ONLY contain a string that summarizes anything interesting that the agent may have noticed'
        output = self._run_v2(prompt,
                              example_output,
                              special_instruction)
        logger.info(f"Run action: {self.__class__.__name__} with result: {output}")

        return output

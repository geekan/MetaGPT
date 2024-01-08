"""
Filename: MetaGPT/metagpt/provider/human_provider.py
Created Date: Wednesday, November 8th 2023, 11:55:46 pm
Author: garylin2099
"""
from typing import Optional

from metagpt.configs.llm_config import LLMConfig
from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM


class HumanProvider(BaseLLM):
    """Humans provide themselves as a 'model', which actually takes in human input as its response.
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction
    """

    def __init__(self, config: LLMConfig):
        pass

    def ask(self, msg: str, timeout=3) -> str:
        logger.info("It's your turn, please type in your response. You may also refer to the context below")
        rsp = input(msg)
        if rsp in ["exit", "quit"]:
            exit()
        return rsp

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        generator: bool = False,
        timeout=3,
    ) -> str:
        return self.ask(msg, timeout=timeout)

    async def acompletion(self, messages: list[dict], timeout=3):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """dummy implementation of abstract method in base"""
        return ""

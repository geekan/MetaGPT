"""
Filename: MetaGPT/metagpt/provider/human_provider.py
Created Date: Wednesday, November 8th 2023, 11:55:46 pm
Author: garylin2099
"""
from typing import Optional

from metagpt.configs.llm_config import LLMConfig
from metagpt.const import LLM_API_TIMEOUT, USE_CONFIG_TIMEOUT
from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM


class HumanProvider(BaseLLM):
    """Humans provide themselves as a 'model', which actually takes in human input as its response.
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    def ask(self, msg: str, timeout=USE_CONFIG_TIMEOUT) -> str:
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
        timeout=USE_CONFIG_TIMEOUT,
        **kwargs
    ) -> str:
        return self.ask(msg, timeout=self.get_timeout(timeout))

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        pass

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """dummy implementation of abstract method in base"""
        return []

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        pass

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=USE_CONFIG_TIMEOUT) -> str:
        """dummy implementation of abstract method in base"""
        return ""

    def get_timeout(self, timeout: int) -> int:
        return timeout or LLM_API_TIMEOUT

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
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction.

    Args:
        config: Configuration for the LLM.

    """

    def __init__(self, config: LLMConfig):
        pass

    def ask(self, msg: str, timeout=3) -> str:
        """Simulates asking a question to a human.

        Args:
            msg: The message or question to ask.
            timeout: The time in seconds to wait for a response. Defaults to 3.

        Returns:
            The response from the human.
        """
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
        """Asynchronously simulates asking a question to a human.

        Args:
            msg: The message or question to ask.
            system_msgs: Optional system messages.
            format_msgs: Optional formatted messages.
            generator: Flag to indicate if a generator is used. Defaults to False.
            timeout: The time in seconds to wait for a response. Defaults to 3.

        Returns:
            The response from the human.
        """
        return self.ask(msg, timeout=timeout)

    async def acompletion(self, messages: list[dict], timeout=3):
        """Dummy implementation of abstract method in base.

        Args:
            messages: The messages to process.
            timeout: The time in seconds to wait for completion. Defaults to 3.

        Returns:
            An empty list.
        """
        return []

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """Dummy implementation of abstract method in base.

        Args:
            messages: The messages to process.
            stream: Flag to indicate if streaming is used. Defaults to False.
            timeout: The time in seconds to wait for completion. Defaults to 3.

        Returns:
            An empty string.
        """
        return ""

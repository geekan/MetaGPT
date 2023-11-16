'''
Filename: MetaGPT/metagpt/provider/human_provider.py
Created Date: Wednesday, November 8th 2023, 11:55:46 pm
Author: garylin2099
'''
from typing import Optional
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.logs import logger

class HumanProvider(BaseGPTAPI):
    """Humans provide themselves as a 'model', which actually takes in human input as its response.
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction
    """

    def ask(self, msg: str) -> str:
        logger.info("It's your turn, please type in your response. You may also refer to the context below")
        rsp = input(msg)
        if rsp in ["exit", "quit"]:
            exit()
        return rsp

    async def aask(self, msg: str, system_msgs: Optional[list[str]] = None) -> str:
        return self.ask(msg)

    def completion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """dummy implementation of abstract method in base"""
        return []

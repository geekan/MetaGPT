#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : tutorial_assistant.py
@Describe : Actions of the tutorial assistant, including writing directories and document content.
"""

from typing import Dict

from metagpt.actions import Action
from metagpt.prompts.tutorial_assistant import CONTENT_PROMPT, DIRECTORY_PROMPT
from metagpt.utils.common import OutputParser


class WriteDirectory(Action):
    """Action class for writing tutorial directories.

    Args:
        name: The name of the action.
        language: The language to output, default is "Chinese".
    """

    name: str = "WriteDirectory"
    language: str = "Chinese"

    async def run(self, topic: str, *args, **kwargs) -> Dict:
        """Execute the action to generate a tutorial directory according to the topic.

        Args:
            topic: The tutorial topic.

        Returns:
            the tutorial directory information, including {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}.
        """
        prompt = DIRECTORY_PROMPT.format(topic=topic, language=self.language)
        resp = await self._aask(prompt=prompt)
        return OutputParser.extract_struct(resp, dict)


class WriteContent(Action):
    """Action class for writing tutorial content.

    Args:
        name: The name of the action.
        directory: The content to write.
        language: The language to output, default is "Chinese".
    """

    name: str = "WriteContent"
    directory: dict = dict()
    language: str = "Chinese"

    async def run(self, topic: str, *args, **kwargs) -> str:
        """Execute the action to write document content according to the directory and topic.

        Args:
            topic: The tutorial topic.

        Returns:
            The written tutorial content.
        """
        prompt = CONTENT_PROMPT.format(topic=topic, language=self.language, directory=self.directory)
        return await self._aask(prompt=prompt)

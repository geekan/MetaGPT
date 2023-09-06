#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : tutorial_assistant.py
@Describe : Actions of the tutorial assistant, including writing directories and document content.
"""
import json
from datetime import datetime
from typing import Dict

import aiofiles

from metagpt.actions import Action
from metagpt.const import TUTORIAL_PATH
from metagpt.logs import logger
from metagpt.prompts.tutorial_assistant import DIRECTORY_PROMPT, CONTENT_PROMPT


class WriteDirectory(Action):
    """Action class for writing tutorial directories.

    Args:
        name: The name of the action.
        language: The language to output, default is "Chinese".
    """

    def __init__(self, name: str = "", language: str = "Chinese", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.language = language

    async def run(self, topic: str, *args, **kwargs) -> Dict:
        """Execute the action to generate a tutorial directory according to the topic.

        Args:
            topic: The tutorial topic.

        Returns:
            the tutorial directory information, such as {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}
        """
        prompt = DIRECTORY_PROMPT.format(topic=topic, language=self.language)
        directory = await self._aask(prompt=prompt)
        return json.loads(directory)


class WriteContent(Action):
    """Action class for writing tutorial content.

    Args:
        name: The name of the action.
        directory: The content to write.
        language: The language to output, default is "Chinese".
    """

    def __init__(self, name: str = "", directory: str = "", language: str = "Chinese", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.language = language
        self.directory = directory

    async def run(self, topic: str, *args, **kwargs) -> str:
        """Execute the action to write document content according to the directory and topic.

        Args:
            topic: The tutorial topic.

        Returns:
            The written tutorial content.
        """
        prompt = CONTENT_PROMPT.format(topic=topic, language=self.language, directory=self.directory)
        return await self._aask(prompt=prompt)


class SaveDocx(Action):
    """Action class for saving tutorial docx.

    Args:
        name: The name of the action.
    """

    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def run(self, title: str, content: str, *args, **kwargs) -> str:
        """Execute the action to save the generated tutorial document to a Markdown file.

        Args:
            title: The title of tutorial.
            content: The total content of tutorial.

        Returns:
            The full filename of tutorial content.

        """
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        pathname = TUTORIAL_PATH / current_time
        pathname.mkdir(parents=True, exist_ok=True)
        filename = f"{pathname}/{title}.md"
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as writer:
            await writer.write(content)
            logger.info(f"Successfully write docx: {filename}")
            return filename
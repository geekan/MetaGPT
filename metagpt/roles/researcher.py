#!/usr/bin/env python
"""
@Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false indicates that further reasoning cannot continue.
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, change the data type of
        the `cause_by` value in the `Message` to a string to support the new message distribution feature.
"""

import asyncio
import re

from pydantic import BaseModel

from metagpt.actions import Action, CollectLinks, ConductResearch, WebBrowseAndSummarize
from metagpt.actions.research import get_research_system_text
from metagpt.const import RESEARCH_PATH
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


class Report(BaseModel):
    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""


class Researcher(Role):
    name: str = "David"
    profile: str = "Researcher"
    goal: str = "Gather information and conduct research"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "en-us"
    enable_concurrency: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CollectLinks, WebBrowseAndSummarize, ConductResearch])
        self._set_react_mode(RoleReactMode.BY_ORDER.value, len(self.actions))
        if self.language not in ("en-us", "zh-cn"):
            logger.warning(f"The language `{self.language}` has not been tested, it may not work.")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.rc.memory.get(k=1)[0]
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            topic = msg.content

        research_system_text = self.research_system_text(topic, todo)
        if isinstance(todo, CollectLinks):
            links = await todo.run(topic, 4, 4)
            ret = Message(
                content="", instruct_content=Report(topic=topic, links=links), role=self.profile, cause_by=todo
            )
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (todo.run(*url, query=query, system_text=research_system_text) for (query, url) in links.items())
            if self.enable_concurrency:
                summaries = await asyncio.gather(*todos)
            else:
                summaries = [await i for i in todos]
            summaries = list((url, summary) for i in summaries for (url, summary) in i.items() if summary)
            ret = Message(
                content="", instruct_content=Report(topic=topic, summaries=summaries), role=self.profile, cause_by=todo
            )
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(f"url: {url}\nsummary: {summary}" for (url, summary) in summaries)
            content = await self.rc.todo.run(topic, summary_text, system_text=research_system_text)
            ret = Message(
                content="",
                instruct_content=Report(topic=topic, content=content),
                role=self.profile,
                cause_by=self.rc.todo,
            )
        self.rc.memory.add(ret)
        return ret

    def research_system_text(self, topic, current_task: Action) -> str:
        """BACKWARD compatible
        This allows sub-class able to define its own system prompt based on topic.
        return the previous implementation to have backward compatible
        Args:
            topic:
            language:

        Returns: str
        """
        return get_research_system_text(topic, self.language)

    async def react(self) -> Message:
        msg = await super().react()
        report = msg.instruct_content
        self.write_report(report.topic, report.content)
        return msg

    def write_report(self, topic: str, content: str):
        filename = re.sub(r'[\\/:"*?<>|]+', " ", topic)
        filename = filename.replace("\n", "")
        if not RESEARCH_PATH.exists():
            RESEARCH_PATH.mkdir(parents=True)
        filepath = RESEARCH_PATH / f"{filename}.md"
        filepath.write_text(content)


if __name__ == "__main__":
    import fire

    async def main(topic: str, language: str = "en-us", enable_concurrency: bool = True):
        role = Researcher(language=language, enable_concurrency=enable_concurrency)
        await role.run(topic)

    fire.Fire(main)

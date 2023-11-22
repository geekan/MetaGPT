#!/usr/bin/env python

import asyncio

from pydantic import BaseModel

from metagpt.actions import CollectLinks, ConductResearch, WebBrowseAndSummarize
from metagpt.actions.research import get_research_system_text
from metagpt.const import RESEARCH_PATH
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class Report(BaseModel):
    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""


class Researcher(Role):
    def __init__(
        self,
        name: str = "David",
        profile: str = "Researcher",
        goal: str = "Gather information and conduct research",
        constraints: str = "Ensure accuracy and relevance of information",
        language: str = "en-us",
        **kwargs,
    ):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([CollectLinks(name), WebBrowseAndSummarize(name), ConductResearch(name)])
        self._set_react_mode(react_mode="by_order")
        self.language = language
        if language not in ("en-us", "zh-cn"):
            logger.warning(f"The language `{language}` has not been tested, it may not work.")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo
        msg = self._rc.memory.get(k=1)[0]
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            topic = msg.content

        research_system_text = get_research_system_text(topic, self.language)
        if isinstance(todo, CollectLinks):
            links = await todo.run(topic, 4, 4)
            ret = Message("", Report(topic=topic, links=links), role=self.profile, cause_by=type(todo))
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (todo.run(*url, query=query, system_text=research_system_text) for (query, url) in links.items())
            summaries = await asyncio.gather(*todos)
            summaries = list((url, summary) for i in summaries for (url, summary) in i.items() if summary)
            ret = Message("", Report(topic=topic, summaries=summaries), role=self.profile, cause_by=type(todo))
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(f"url: {url}\nsummary: {summary}" for (url, summary) in summaries)
            content = await self._rc.todo.run(topic, summary_text, system_text=research_system_text)
            ret = Message("", Report(topic=topic, content=content), role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(ret)
        return ret

    async def react(self) -> Message:
        msg = await super().react()
        report = msg.instruct_content
        self.write_report(report.topic, report.content)
        return msg

    def write_report(self, topic: str, content: str):
        if not RESEARCH_PATH.exists():
            RESEARCH_PATH.mkdir(parents=True)
        filepath = RESEARCH_PATH / f"{topic}.md"
        filepath.write_text(content)


if __name__ == "__main__":
    import fire

    async def main(topic: str, language="en-us"):
        role = Researcher(topic, language=language)
        await role.run(topic)

    fire.Fire(main)

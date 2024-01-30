#!/usr/bin/env python
# @Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false indicates that further reasoning cannot continue.
# @Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, change the data type of
#         the `cause_by` value in the `Message` to a string to support the new message distribution feature.

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
    """A model for representing a research report.

    Attributes:
        topic: The main topic of the report.
        links: A dictionary mapping queries to lists of URLs.
        summaries: A list of tuples, each containing a URL and its summary.
        content: The final content of the report.
    """

    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""


class Researcher(Role):
    """A role for conducting research on a given topic.

    This role involves collecting links, browsing web pages, summarizing content, and generating a final report.

    Attributes:
        name: The name of the researcher.
        profile: The profile description of the researcher.
        goal: The goal of the researcher.
        constraints: The constraints the researcher operates under.
        language: The language the researcher uses for research.
    """

    name: str = "David"
    profile: str = "Researcher"
    goal: str = "Gather information and conduct research"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "en-us"

    def __init__(self, **kwargs):
        """Initializes the Researcher with specific actions and react mode.

        Args:
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(**kwargs)
        self.set_actions(
            [CollectLinks(name=self.name), WebBrowseAndSummarize(name=self.name), ConductResearch(name=self.name)]
        )
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        if self.language not in ("en-us", "zh-cn"):
            logger.warning(f"The language `{self.language}` has not been tested, it may not work.")

    async def _think(self) -> bool:
        """Determines the next state of the researcher based on current tasks.

        Returns:
            A boolean indicating if there are more tasks to perform.
        """
        if self.rc.todo is None:
            self._set_state(0)
            return True

        if self.rc.state + 1 < len(self.states):
            self._set_state(self.rc.state + 1)
        else:
            self.set_todo(None)
            return False

    async def _act(self) -> Message:
        """Performs the current action based on the todo list and generates a message.

        Returns:
            A message containing the result of the action.
        """
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
            summaries = await asyncio.gather(*todos)
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
        """Generates a system text for research based on the topic and current task.

        Args:
            topic: The research topic.
            current_task: The current action being performed.

        Returns:
            A string containing the system text for research.
        """
        return get_research_system_text(topic, self.language)

    async def react(self) -> Message:
        """Processes the message generated by the act method and writes a report.

        Returns:
            The processed message.
        """
        msg = await super().react()
        report = msg.instruct_content
        self.write_report(report.topic, report.content)
        return msg

    def write_report(self, topic: str, content: str):
        """Writes the research report to a markdown file.

        Args:
            topic: The topic of the report.
            content: The content of the report.
        """
        filename = re.sub(r'[\\/:"*?<>|]+', " ", topic)
        filename = filename.replace("\n", "")
        if not RESEARCH_PATH.exists():
            RESEARCH_PATH.mkdir(parents=True)
        filepath = RESEARCH_PATH / f"{filename}.md"
        filepath.write_text(content)


if __name__ == "__main__":
    import fire

    async def main(topic: str, language="en-us"):
        role = Researcher(language=language)
        await role.run(topic)

    fire.Fire(main)

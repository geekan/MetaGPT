from __future__ import annotations

import asyncio
import re
from enum import Enum
from typing import Tuple

from pydantic import BaseModel

from metagpt.actions import Action
from metagpt.schema import Message


class SOPItemDef(BaseModel):
    """
    Represents an item in a Standard Operating Procedure (SOP).

    Attributes:
        name (str): name of the SOP item.
        description (str): The description or title of the SOP.
        sop (List[str]): The steps or details of the SOP.
    """

    name: str
    description: str
    sop: list[str] = []


class SOPItem(Enum):
    SOFTWARE_DEVELOPMENT = SOPItemDef(
        name="software development",
        description="Software development intention including developing or building software, games, app, websites, etc. EXCLUDING bug fixes, report any issues, environment setup, terminal operations, and pip install.",
        sop=[
            "Writes a PRD based on software requirements.",
            "Writes a design to the project repository, based on the PRD of the project.",
            "Writes a project plan to the project repository, based on the design of the project.",
            "Writes code to implement designed features according to the project plan and adds them to the project repository.",
            "Stage and commit changes for the project repository using Git.",
        ],
    )
    # FIX_BUGS = SOPItemDef(
    #     name="fix bugs",
    #     description="Fix bugs in a given project.",
    #     sop=[
    #         "Fix bugs in the project repository.",
    #         "Stage and commit changes for the project repository using Git.",
    #     ],
    # )
    # FORMAT_REPO = SOPItemDef(
    #     name="format repo",
    #     description="download repository from git and format the project to MetaGPT project",
    #     sop=[
    #         "Imports a project from a Git website and formats it to MetaGPT project format to enable incremental appending requirements.",
    #         "Stage and commit changes for the project repository using Git.",
    #     ],
    # )
    WEB_OPERATION = SOPItemDef(
        name="web operation",
        description="web browsing, scraping, imitation and other interaction with the web",
    )
    OTHER = SOPItemDef(
        name="other",
        description="Other intentions that do not fall into the above categories, including data science, data analysis, machine learning, deep learning and text-to-image etc.",
    )

    @property
    def type_name(self):
        return self.value.name

    @classmethod
    def get_type(cls, type_name):
        for member in cls:
            if member.type_name == type_name:
                return member.value
        return None


DETECT_PROMPT = """
# User Requirement
{user_requirement}
# Intentions
{intentions}
# Task
Classify user requirement into one type of the above intentions, output the index of the intention directly.
Intention index:
"""

REQ_WITH_SOP = """
{user_requirement}
## Knowledge
To meet user requirements, the following standard operating procedure(SOP) must be used:

{sop}
"""


class DetectIntent(Action):
    async def run(self, with_message: Message, **kwargs) -> Tuple[str, str]:
        user_requirement = with_message.content
        mappings = {i + 1: si for i, si in enumerate(SOPItem)}
        intentions = "\n".join([f"{i + 1}. {si.type_name}: {si.value.description}" for i, si in enumerate(SOPItem)])
        prompt = DETECT_PROMPT.format(user_requirement=user_requirement, intentions=intentions)

        rsp = await self._aask(prompt)
        match = re.search(r"\d+", rsp)
        index = len(SOPItem) + 1  # 1-based
        if match:
            index = int(match.group())  # 1-based
        sop = mappings[index].value.sop if index in mappings else None
        sop_type = mappings[index].type_name if index in mappings else SOPItem.OTHER.type_name

        req_with_sop = (
            REQ_WITH_SOP.format(
                user_requirement=user_requirement, sop="\n".join([f"{i + 1}. {v}" for i, v in enumerate(sop)])
            )
            if sop
            else user_requirement
        )

        return req_with_sop, sop_type


async def main():
    # Example usage of the DetectIntent action
    user_requirements = [
        "Develop a 2048 game.",
        "Run data analysis on sklearn wine dataset",
        "帮我把pip的源设置成：https://pypi.tuna.tsinghua.edu.cn/simple",
        "This is a website url does not require login: https://demosc.chinaz.net/Files/DownLoad//moban/202404/moban7767 please write a similar web page,developed in vue language, The package.json dependency must be generated",
        "I would like to imitate the website available at https://demosc.chinaz.net/Files/DownLoad//moban/202404/moban7767. Could you please browse through it?",
    ]
    detect_intent = DetectIntent()

    for user_requirement in user_requirements:
        req_with_sop, sop_type = await detect_intent.run(Message(role="user", content=user_requirement))
        print(req_with_sop)
        print(f"Detected SOP Type: {sop_type}")


if __name__ == "__main__":
    asyncio.run(main())

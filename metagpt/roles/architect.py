#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""
from metagpt.actions import WritePRD
from metagpt.actions.design_api import WriteDesign
from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.software_development import write_trd_and_framework
from metagpt.utils.common import tool2name

ARCHITECT_INSTRUCTION = """
Use WriteDesign tool to write a system design document if a system design is required; Use `write_trd_and_framework` tool to write a software framework if a software framework is required;

Note:
1. When you think, just analyze which tool you should use, and then provide your answer. And your output should contain firstly, secondly, ...
2. The automated tools at your disposal will generate a document that perfectly meets your requirements. There is no need to do it manually.
"""


class Architect(RoleZero):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
    """

    name: str = "Bob"
    profile: str = "Architect"
    goal: str = "design a concise, usable, complete software system. ouput the system design or software framework."
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )

    instruction: str = ARCHITECT_INSTRUCTION
    max_react_loop: int = 1  # FIXME: Read and edit files requires more steps, consider later
    tools: list[str] = [
        "Editor:write,read,write_content",
        "RoleZero",
        "WriteDesign",
        write_trd_and_framework.__name__,
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        # Initialize actions specific to the Architect role
        self.set_actions([WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WritePRD})

    def _update_tool_execution(self):
        write_design = WriteDesign()
        self.tool_execution_map.update(tool2name(WriteDesign, ["run"], write_design.run))
        self.tool_execution_map.update(
            {
                write_trd_and_framework.__name__: write_trd_and_framework,
                "run": write_design.run,  # alias
            }
        )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""
from pydantic import Field

from metagpt.actions.design_api import WriteDesign
from metagpt.actions.write_prd import WritePRD
from metagpt.prompts.di.architect import ARCHITECT_EXAMPLE, ARCHITECT_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.terminal import Terminal


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
    goal: str = "design a concise, usable, complete software system. output the system design."
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )
    terminal: Terminal = Field(default_factory=Terminal, exclude=True)
    instruction: str = ARCHITECT_INSTRUCTION
    tools: list[str] = [
        "Editor:write,read,similarity_search",
        "RoleZero",
        "Terminal:run_command",
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        # Initialize actions specific to the Architect role
        self.set_actions([WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WritePRD})

    def _retrieve_experience(self) -> str:
        return ARCHITECT_EXAMPLE

    def _update_tool_execution(self):
        self.tool_execution_map.update({"Terminal.run_command": self.terminal.run_command})

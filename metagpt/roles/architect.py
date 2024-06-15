#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""
from metagpt.actions import WritePRD
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.requirement_analysis.framework import (
    EvaluateFramework,
    WriteFramework,
)
from metagpt.actions.requirement_analysis.trd import (
    CompressExternalInterfaces,
    DetectInteraction,
    EvaluateTRD,
    WriteTRD,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.utils.common import tool2name


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
    goal: str = "design a concise, usable, complete software system"
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )

    instruction: str = """Use WriteDesign tool to write a system design document if a system design is required; Use WriteTRD tool to write a TRD if a TRD is required;"""
    max_react_loop: int = 1  # FIXME: Read and edit files requires more steps, consider later
    tools: list[str] = [
        "Editor:write,read,write_content",
        "RoleZero",
        "WriteDesign",
        "CompressExternalInterfaces",
        "DetectInteraction",
        "EvaluateTRD",
        "WriteTRD",
        "WriteFramework",
        "EvaluateFramework",
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
        compress_external_interfaces = CompressExternalInterfaces()
        self.tool_execution_map.update(tool2name(CompressExternalInterfaces, ["run"], compress_external_interfaces.run))
        detect_interaction = DetectInteraction()
        self.tool_execution_map.update(tool2name(DetectInteraction, ["run"], detect_interaction.run))
        evaluate_trd = EvaluateTRD()
        self.tool_execution_map.update(tool2name(EvaluateTRD, ["run"], evaluate_trd.run))
        write_trd = WriteTRD()
        self.tool_execution_map.update(tool2name(WriteTRD, ["run"], write_trd.run))
        write_framework = WriteFramework()
        self.tool_execution_map.update(tool2name(WriteFramework, ["run"], write_framework.run))
        evaluate_framework = EvaluateFramework()
        self.tool_execution_map.update(tool2name(EvaluateFramework, ["run"], evaluate_framework.run))

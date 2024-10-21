#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from metagpt.actions import WriteTasks
from metagpt.actions.design_api import WriteDesign
from metagpt.roles.di.role_zero import RoleZero


class ProjectManager(RoleZero):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    name: str = "Eve"
    profile: str = "Project Manager"
    goal: str = (
        "break down tasks according to PRD/technical design, generate a task list, and analyze task "
        "dependencies to start with the prerequisite modules"
    )
    constraints: str = "use same language as user requirement"

    instruction: str = """Use WriteTasks tool to write a project task list"""
    max_react_loop: int = 1  # FIXME: Read and edit files requires more steps, consider later
    tools: list[str] = ["Editor:write,read,similarity_search", "RoleZero", "WriteTasks"]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        self.set_actions([WriteTasks])
        self._watch([WriteDesign])

    def _update_tool_execution(self):
        wt = WriteTasks()
        self.tool_execution_map.update(
            {
                "WriteTasks.run": wt.run,
                "WriteTasks": wt.run,  # alias
            }
        )

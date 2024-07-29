#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
@Modified By: mashenquan, 2023/11/27. Add `PrepareDocuments` action according to Section 2.2.3.5.1 of RFC 135.
"""

from metagpt.actions import UserRequirement, WritePRD
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.actions.requirement_analysis.requirement.pic2txt import Pic2Txt
from metagpt.roles.di.role_zero import RoleZero
from metagpt.roles.role import RoleReactMode
from metagpt.utils.common import any_to_name, any_to_str, tool2name
from metagpt.utils.git_repository import GitRepository


class ProductManager(RoleZero):
    """
    Represents a Product Manager role responsible for product development and management.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """

    name: str = "Alice"
    profile: str = "Product Manager"
    goal: str = "efficiently create a successful product that meets market demands and user expectations. Create a Product Requirement Document."
    constraints: str = "utilize the same language as the user requirements for seamless communication"
    todo_action: str = any_to_name(WritePRD)

    instruction: str = """Use WritePRD tool to write PRD if a PRD is required, users may asks for a software without mentioning PRD, but you should output the PRD of that software; Use `Pic2Txt` tool to write out an intact textual user requirements if an intact textual user requiremnt is required given some images alongside the contextual textual descriptions"""
    max_react_loop: int = 1  # FIXME: Read and edit files requires more steps, consider later
    tools: list[str] = ["RoleZero", "WritePRD", Pic2Txt.__name__]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        self.set_actions([PrepareDocuments(send_to=any_to_str(self)), WritePRD])
        self._watch([UserRequirement, PrepareDocuments])
        if self.use_fixed_sop:
            self.rc.react_mode = RoleReactMode.BY_ORDER

    def _update_tool_execution(self):
        wp = WritePRD()
        self.tool_execution_map.update(tool2name(WritePRD, ["run"], wp.run))
        pic2txt = Pic2Txt()
        self.tool_execution_map.update(tool2name(Pic2Txt, ["run"], pic2txt.run))

    async def _think(self) -> bool:
        """Decide what to do"""
        if not self.use_fixed_sop:
            return await super()._think()

        if GitRepository.is_git_dir(self.config.project_path) and not self.config.git_reinit:
            self._set_state(1)
        else:
            self._set_state(0)
            self.config.git_reinit = False
            self.todo_action = any_to_name(WritePRD)
        return bool(self.rc.todo)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:44
@Author  : alexanderwu
@File    : __init__.py
"""
from enum import Enum

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.add_requirement import BossRequirement
from metagpt.actions.debug_error import DebugError
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.design_api_review import DesignReview
from metagpt.actions.design_filenames import DesignFilenames
from metagpt.actions.project_management import AssignTasks, WriteTasks
from metagpt.actions.research import CollectLinks, WebBrowseAndSummarize, ConductResearch
from metagpt.actions.run_code import RunCode
from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_review import WriteCodeReview
from metagpt.actions.write_prd import WritePRD
from metagpt.actions.write_prd_review import WritePRDReview
from metagpt.actions.write_test import WriteTest


class ActionType(Enum):
    """All types of Actions, used for indexing."""

    ADD_REQUIREMENT = BossRequirement
    WRITE_PRD = WritePRD
    WRITE_PRD_REVIEW = WritePRDReview
    WRITE_DESIGN = WriteDesign
    DESIGN_REVIEW = DesignReview
    DESIGN_FILENAMES = DesignFilenames
    WRTIE_CODE = WriteCode
    WRITE_CODE_REVIEW = WriteCodeReview
    WRITE_TEST = WriteTest
    RUN_CODE = RunCode
    DEBUG_ERROR = DebugError
    WRITE_TASKS = WriteTasks
    ASSIGN_TASKS = AssignTasks
    SEARCH_AND_SUMMARIZE = SearchAndSummarize
    COLLECT_LINKS = CollectLinks
    WEB_BROWSE_AND_SUMMARIZE = WebBrowseAndSummarize
    CONDUCT_RESEARCH = ConductResearch


__all__ = [
    "ActionType",
    "Action",
    "ActionOutput",
]

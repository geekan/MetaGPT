#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional

from metagpt.const import BUGFIX_FILENAME, REQUIREMENT_FILENAME
from metagpt.schema import BugFixContext, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import any_to_str


@register_tool(tags=["software company", "ProductManager"])
async def write_prd(idea: str, project_path: Optional[str | Path] = None) -> Path:
    """Writes a PRD based on user requirements.

    Args:
        idea (str): The idea or concept for the PRD.
        project_path (Optional[str|Path], optional): The path to an existing project directory created by `write_prd`.
            If it's None, a new project path will be created. Defaults to None.

    Returns:
        Path: The path to the PRD files under the project directory

    Example:
        >>> # Create a new project:
        >>> from metagpt.tools.libs.software_development import write_prd
        >>> prd_path = await write_prd("Create a new feature for the application")
        >>> print(prd_path)
        '/path/to/project_path/docs/prd/'

        >>> # Add user requirements to the exists project:
        >>> from metagpt.tools.libs.software_development import write_prd
        >>> project_path = '/path/to/exists_project_path'
        >>> prd_path = await write_prd("Create a new feature for the application", project_path=project_path)
        >>> print(prd_path = )
        '/path/to/project_path/docs/prd/'
    """
    from metagpt.actions import UserRequirement
    from metagpt.context import Context
    from metagpt.roles import ProductManager

    ctx = Context()
    if project_path:
        ctx.config.project_path = Path(project_path)
        ctx.config.inc = True
    role = ProductManager(context=ctx)
    msg = await role.run(with_message=Message(content=idea, cause_by=UserRequirement))
    await role.run(with_message=msg)
    return ctx.repo.docs.prd.workdir


@register_tool(tags=["software company", "Architect"])
async def write_design(prd_path: str | Path) -> Path:
    """Writes a design to the project repository, based on the PRD of the project.

    Args:
        prd_path (str|Path): The path to the PRD files under the project directory.

    Returns:
        Path: The path to the system design files under the project directory.

    Example:
        >>> from metagpt.tools.libs.software_development import write_design
        >>> prd_path = '/path/to/project_path/docs/prd' # Returned by `write_prd`
        >>> system_design_path = await write_desgin(prd_path)
        >>> print(system_design_path)
        '/path/to/project_path/docs/system_design/'

    """
    from metagpt.actions import WritePRD
    from metagpt.context import Context
    from metagpt.roles import Architect

    ctx = Context()
    project_path = Path(prd_path).parent.parent
    ctx.set_repo_dir(project_path)

    role = Architect(context=ctx)
    await role.run(with_message=Message(content="", cause_by=WritePRD))
    return ctx.repo.docs.system_design.workdir


@register_tool(tags=["software company", "Architect"])
async def write_project_plan(system_design_path: str | Path) -> Path:
    """Writes a project plan to the project repository, based on the design of the project.

    Args:
        system_design_path (str|Path): The path to the system design files under the project directory.

    Returns:
        Path: The path to task files under the project directory.

    Example:
        >>> from metagpt.tools.libs.software_development import write_project_plan
        >>> system_design_path = '/path/to/project_path/docs/system_design/' # Returned by `write_design`
        >>> task_path = await write_project_plan(system_design_path)
        >>> print(task_path)
        '/path/to/project_path/docs/task'

    """
    from metagpt.actions import WriteDesign
    from metagpt.context import Context
    from metagpt.roles import ProjectManager

    ctx = Context()
    project_path = Path(system_design_path).parent.parent
    ctx.set_repo_dir(project_path)

    role = ProjectManager(context=ctx)
    await role.run(with_message=Message(content="", cause_by=WriteDesign))
    return ctx.repo.docs.task.workdir


@register_tool(tags=["software company", "Engineer"])
async def write_codes(task_path: str | Path, inc: bool = False) -> Path:
    """Writes codes to the project repository, based on the project plan of the project.

    Args:
        task_path (str|Path): The path to task files under the project directory.
        inc (bool, optional): Whether to write incremental codes. Defaults to False.

    Returns:
        Path: The path to the source code files under the project directory.

    Example:
        # Write codes to a new project
        >>> from metagpt.tools.libs.software_development import write_codes
        >>> task_path = '/path/to/project_path/docs/task' # Returned by `write_project_plan`
        >>> src_path = await write_codes(task_path)
        >>> print(src_path)
        '/path/to/project_path/src/'

        # Write increment codes to the exists project
        >>> from metagpt.tools.libs.software_development import write_codes
        >>> task_path = '/path/to/project_path/docs/task' # Returned by `write_prd`
        >>> src_path = await write_codes(task_path, inc=True)
        >>> print(src_path)
        '/path/to/project_path/src/'
    """
    from metagpt.actions import WriteTasks
    from metagpt.context import Context
    from metagpt.roles import Engineer

    ctx = Context()
    ctx.config.inc = inc
    project_path = Path(task_path).parent.parent
    ctx.set_repo_dir(project_path)

    role = Engineer(context=ctx)
    msg = Message(content="", cause_by=WriteTasks, send_to=role)
    me = {any_to_str(role), role.name}
    while me.intersection(msg.send_to):
        msg = await role.run(with_message=msg)
    return ctx.repo.srcs.workdir


@register_tool(tags=["software company", "QaEngineer"])
async def run_qa_test(src_path: str | Path) -> Path:
    """Run QA test on the project repository.

    Args:
        src_path (str|Path): The path to the source code files under the project directory.

    Returns:
        Path: The path to the unit tests under the project directory

    Example:
        >>> from metagpt.tools.libs.software_development import run_qa_test
        >>> src_path = '/path/to/project_path/src/' # Returned by `write_codes`
        >>> test_path = await run_qa_test(src_path)
        >>> print(test_path)
        '/path/to/project_path/tests'
    """
    from metagpt.actions.summarize_code import SummarizeCode
    from metagpt.context import Context
    from metagpt.environment import Environment
    from metagpt.roles import QaEngineer

    ctx = Context()
    project_path = Path(src_path).parent
    ctx.set_repo_dir(project_path)
    ctx.src_workspace = ctx.git_repo.workdir / ctx.git_repo.workdir.name

    env = Environment(context=ctx)
    role = QaEngineer(context=ctx)
    env.add_role(role)

    msg = Message(content="", cause_by=SummarizeCode, send_to=role)
    env.publish_message(msg)

    while not env.is_idle:
        await env.run()
    return ctx.repo.tests.workdir


@register_tool(tags=["software company", "Engineer"])
async def fix_bug(project_path: str | Path, issue: str) -> Path:
    """Fix bugs in the project repository.

    Args:
        project_path (str|Path): The path to the project repository.
        issue (str): Description of the bug or issue.

    Returns:
        Path: The path to the project directory

    Example:
        >>> from metagpt.tools.libs.software_development import fix_bug
        >>> project_path = '/path/to/project_path' # Returned by `write_codes`
        >>> issue = 'Exception: exception about ...; Bug: bug about ...; Issue: issue about ...'
        >>> project_path = await fix_bug(project_path=project_path, issue=issue)
        >>> print(project_path)
        '/path/to/project_path'
    """
    from metagpt.actions.fix_bug import FixBug
    from metagpt.context import Context
    from metagpt.roles import Engineer

    ctx = Context()
    ctx.set_repo_dir(project_path)
    ctx.src_workspace = ctx.git_repo.workdir / ctx.git_repo.workdir.name
    await ctx.repo.docs.save(filename=BUGFIX_FILENAME, content=issue)
    await ctx.repo.docs.save(filename=REQUIREMENT_FILENAME, content="")

    role = Engineer(context=ctx)
    bug_fix = BugFixContext(filename=BUGFIX_FILENAME)
    msg = Message(
        content=bug_fix.model_dump_json(),
        instruct_content=bug_fix,
        role="",
        cause_by=FixBug,
        sent_from=role,
        send_to=role,
    )
    me = {any_to_str(role), role.name}
    while me.intersection(msg.send_to):
        msg = await role.run(with_message=msg)
    return project_path


@register_tool(tags=["software company", "git"])
async def git_archive(project_path: str | Path) -> str:
    """Stage and commit changes for the project repository using Git.

    Args:
        project_path (str|Path): The path to the project repository.


    Returns:
        git log

    Example:
        >>> from metagpt.tools.libs.software_development import git_archive
        >>> project_path = '/path/to/project_path' # Returned by `write_prd`
        >>> git_log = await git_archive(project_path=project_path)
        >>> print(git_log)
        commit a221d1c418c07f2b4fc07001e486285ead1a520a (HEAD -> feature/toollib/software_company, geekan/main)
        Merge: e01afd09 4a72f398
        Author: Sirui Hong <x@xx.github.com>
        Date:   Tue Mar 19 15:16:03 2024 +0800
        Merge pull request #1037 from iorisa/fixbug/issues/1018
        fixbug: #1018

    """
    from metagpt.context import Context

    ctx = Context()
    ctx.set_repo_dir(project_path)
    ctx.git_repo.archive()
    return ctx.git_repo.log()

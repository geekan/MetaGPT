#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import shutil
from pathlib import Path

import typer

from metagpt.actions.rebuild_class_view import RebuildClassView
from metagpt.actions.rebuild_sequence_view import RebuildSequenceView
from metagpt.context import Context
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.git_repository import GitRepository
from metagpt.utils.project_repo import ProjectRepo

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command("", help="Python project reverse engineering.")
def startup(
    project_root: str = typer.Argument(
        default="",
        help="Specify the root directory of the existing project for reverse engineering.",
    ),
    output_dir: str = typer.Option(default="", help="Specify the output directory path for reverse engineering."),
):
    package_root = Path(project_root)
    if not package_root.exists():
        raise FileNotFoundError(f"{project_root} not exists")
    if not _is_python_package_root(package_root):
        raise FileNotFoundError(f'There are no "*.py" files under "{project_root}".')
    init_file = package_root / "__init__.py"  # used by pyreverse
    init_file_exists = init_file.exists()
    if not init_file_exists:
        init_file.touch()

    if not output_dir:
        output_dir = package_root / "../reverse_engineering_output"
    logger.info(f"output dir:{output_dir}")
    try:
        asyncio.run(reverse_engineering(package_root, Path(output_dir)))
    finally:
        if not init_file_exists:
            init_file.unlink(missing_ok=True)
        tmp_dir = package_root / "__dot__"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _is_python_package_root(package_root: Path) -> bool:
    for file_path in package_root.iterdir():
        if file_path.is_file():
            if file_path.suffix == ".py":
                return True
    return False


async def reverse_engineering(package_root: Path, output_dir: Path):
    ctx = Context()
    ctx.git_repo = GitRepository(output_dir)
    ctx.repo = ProjectRepo(ctx.git_repo)
    action = RebuildClassView(name="ReverseEngineering", i_context=str(package_root), llm=LLM(), context=ctx)
    await action.run()

    action = RebuildSequenceView(name="ReverseEngineering", llm=LLM(), context=ctx)
    await action.run()


if __name__ == "__main__":
    app()

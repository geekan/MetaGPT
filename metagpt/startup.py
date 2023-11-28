#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import typer

app = typer.Typer()


@app.command()
def startup(
    idea: str = typer.Argument(..., help="Your innovative idea, such as 'Create a 2048 game.'"),
    investment: float = typer.Option(3.0, help="Dollar amount to invest in the AI company."),
    n_round: int = typer.Option(5, help="Number of rounds for the simulation."),
    code_review: bool = typer.Option(True, help="Whether to use code review."),
    run_tests: bool = typer.Option(False, help="Whether to enable QA for adding & running tests."),
    implement: bool = typer.Option(True, help="Enable or disable code implementation."),
    project_name: str = typer.Option("", help="Unique project name, such as 'game_2048'."),
    inc: bool = typer.Option(False, help="Incremental mode. Use it to coop with existing repo."),
):
    """Run a startup. Be a boss."""
    from metagpt.roles import (
        Architect,
        Engineer,
        ProductManager,
        ProjectManager,
        QaEngineer,
    )
    from metagpt.team import Team

    company = Team()
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
        ]
    )

    if implement or code_review:
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])

    if run_tests:
        company.hire([QaEngineer()])

    company.invest(investment)
    company.run_project(idea, project_name=project_name, inc=inc)
    asyncio.run(company.run(n_round=n_round))


if __name__ == "__main__":
    startup(idea="Make a 2048 game.")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : write_project_framework.py
@Desc    : The implementation of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
import asyncio
import json
import uuid
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List

import typer
from pydantic import BaseModel

from metagpt.config2 import Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles import Architect
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import AIMessage, UserMessage
from metagpt.strategy.experience_retriever import TRDToolExpRetriever
from metagpt.utils.common import aread

app = typer.Typer(add_completion=False)


class EnvBuilder(BaseModel):
    context: Context
    user_requirements: List[str]
    actors: Dict[str, str]
    technical_constraint: str
    output_dir: Path

    def build(self) -> Environment:
        env = MGXEnv(context=self.context)
        team_leader = TeamLeader()
        architect = Architect(experience_retriever=TRDToolExpRetriever())

        # Prepare context
        use_case_actors = "".join([f"- {v}: {k}\n" for k, v in self.actors.items()])
        msg = """
The content of "Actor, System, External System" provides an explanation of actors and systems that appear in UML Use Case diagram.
## Actor, System, External System
{use_case_actors}
        """
        architect.rc.memory.add(AIMessage(content=msg.format(use_case_actors=use_case_actors)))

        # Prepare technical requirements
        msg = """
"Additional Technical Requirements" specifies the additional technical requirements that the generated software framework code must meet.
## Additional Technical Requirements
{technical_requirements}
"""
        architect.rc.memory.add(AIMessage(content=msg.format(technical_requirements=self.technical_constraint)))

        env.add_roles([team_leader, architect])
        return env


async def develop(
    context: Context,
    user_requirement_filename: str,
    actors_filename: str,
    constraint_filename: str,
    output_dir: str,
):
    output_dir = Path(output_dir) if output_dir else DEFAULT_WORKSPACE_ROOT / uuid.uuid4().hex

    v = await aread(filename=user_requirement_filename)
    try:
        user_requirements = json.loads(v)
    except JSONDecodeError:
        user_requirements = [v]
    v = await aread(filename=actors_filename)
    actors = json.loads(v)
    technical_constraint = await aread(filename=constraint_filename)
    env_builder = EnvBuilder(
        context=context,
        user_requirements=user_requirements,
        actors=actors,
        technical_constraint=technical_constraint,
        output_dir=output_dir,
    )
    env = env_builder.build()
    msg = """
Given the user requirement of "User Requirements", write out the software framework.
## User Requirements
{user_requirements}
    """
    env.publish_message(
        UserMessage(content=msg.format(user_requirements="\n".join(user_requirements)), send_to="Bob"),
        user_defined_recipient="Bob",
    )

    while not env.is_idle:
        await env.run()


@app.command()
def startup(
    user_requirement_filename: str = typer.Argument(..., help="The filename of the user requirements."),
    actors_filename: str = typer.Argument(..., help="The filename of UML use case actors description."),
    llm_config: str = typer.Option(default="", help="Low-cost LLM config"),
    constraint_filename: str = typer.Option(default="", help="What technical dependency constraints are."),
    output_dir: str = typer.Option(default="", help="Output directory."),
):
    if llm_config and Path(llm_config).exists():
        config = Config.from_yaml_file(Path(llm_config))
    else:
        logger.info("GPT 4 turbo is recommended")
        config = Config.default()
    ctx = Context(config=config)

    asyncio.run(develop(ctx, user_requirement_filename, actors_filename, constraint_filename, output_dir))


if __name__ == "__main__":
    app()

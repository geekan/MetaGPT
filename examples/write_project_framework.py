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
from pathlib import Path
from typing import Dict, List

import typer

from metagpt.actions.requirement_analysis.framework import (
    EvaluateFramework,
    WriteFramework,
    save_framework,
)
from metagpt.actions.requirement_analysis.trd import (
    CompressExternalInterfaces,
    DetectInteraction,
    EvaluateTRD,
    WriteTRD,
)
from metagpt.config2 import Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.utils.common import aread

app = typer.Typer(add_completion=False)


async def _write_trd(
    context: Context, actors: Dict[str, str], user_requirements: List[str], available_external_interfaces: str
) -> (str, str):
    detect_interaction = DetectInteraction(context=context)
    write_trd = WriteTRD(context=context)
    evaluate_trd = EvaluateTRD(context=context)
    use_case_actors = "".join([f"- {v}: {k}\n" for k, v in actors.items()])
    legacy_user_requirements = []
    legacy_user_requirements_interaction_events = []
    legacy_user_requirements_trd = ""
    for ix, r in enumerate(user_requirements):
        is_pass = False
        evaluation_conclusion = ""
        interaction_events = ""
        trd = ""
        while not is_pass:
            interaction_events = await detect_interaction.run(
                user_requirements=r,
                use_case_actors=use_case_actors,
                legacy_interaction_events=interaction_events,
                evaluation_conclusion=evaluation_conclusion,
            )
            if ix == 0:
                trd = await write_trd.run(
                    user_requirements=r,
                    use_case_actors=use_case_actors,
                    available_external_interfaces=available_external_interfaces,
                    previous_version_trd=trd,
                    evaluation_conclusion=evaluation_conclusion,
                    interaction_events=interaction_events,
                )
                evaluation = await evaluate_trd.run(
                    user_requirements=r, use_case_actors=use_case_actors, trd=trd, interaction_events=interaction_events
                )
            else:
                trd = await write_trd.run(
                    legacy_user_requirements="\n".join(legacy_user_requirements),
                    use_case_actors=use_case_actors,
                    available_external_interfaces=available_external_interfaces,
                    legacy_user_requirements_trd=legacy_user_requirements_trd,
                    legacy_user_requirements_interaction_events="\n".join(legacy_user_requirements_interaction_events),
                    incremental_user_requirements=r,
                    previous_version_trd=trd,
                    evaluation_conclusion=evaluation_conclusion,
                    incremental_user_requirements_interaction_events=interaction_events,
                )
                evaluation = await evaluate_trd.run(
                    user_requirements=r,
                    use_case_actors=use_case_actors,
                    trd=trd,
                    legacy_user_requirements_interaction_events="\n".join(legacy_user_requirements_interaction_events),
                    incremental_user_requirements_interaction_events=interaction_events,
                )
            is_pass = evaluation.is_pass
            evaluation_conclusion = evaluation.conclusion
        legacy_user_requirements.append(r)
        legacy_user_requirements_interaction_events.append(interaction_events)
        legacy_user_requirements_trd = trd

    return use_case_actors, legacy_user_requirements_trd


async def _write_framework(context: Context, use_case_actors: str, trd: str, acknowledge: str, constraint: str) -> str:
    write_framework = WriteFramework(context=context)
    evaluate_framework = EvaluateFramework(context=context)
    is_pass = False
    framework = ""
    evaluation_conclusion = ""
    while not is_pass:
        try:
            framework = await write_framework.run(
                use_case_actors=use_case_actors,
                trd=trd,
                acknowledge=acknowledge,
                legacy_output=framework,
                evaluation_conclusion=evaluation_conclusion,
                additional_technical_requirements=constraint,
            )
        except Exception as e:
            logger.info(f"{e}")
            break
        evaluation = await evaluate_framework.run(
            use_case_actors=use_case_actors,
            trd=trd,
            acknowledge=acknowledge,
            legacy_output=framework,
            additional_technical_requirements=constraint,
        )
        is_pass = evaluation.is_pass
        evaluation_conclusion = evaluation.conclusion
    return framework


async def develop(
    context: Context,
    user_requirement_filename: str,
    actors_filename: str,
    acknowledge_filename: str,
    constraint_filename: str,
    output_dir: str,
):
    output_dir = Path(output_dir) if output_dir else DEFAULT_WORKSPACE_ROOT / uuid.uuid4().hex

    v = await aread(filename=user_requirement_filename)
    user_requirements = json.loads(v)
    v = await aread(filename=actors_filename)
    actors = json.loads(v)
    acknowledge = await aread(filename=acknowledge_filename)
    technical_constraint = await aread(filename=constraint_filename)

    # Compress acknowledge
    compress_acknowledge = CompressExternalInterfaces(context=context)
    available_external_interfaces = await compress_acknowledge.run(acknowledge=acknowledge)

    # Write TRD
    use_case_actors, trd = await _write_trd(
        context=context,
        actors=actors,
        user_requirements=user_requirements,
        available_external_interfaces=available_external_interfaces,
    )

    # Write framework
    framework = await _write_framework(
        context=context,
        use_case_actors=use_case_actors,
        trd=trd,
        acknowledge=acknowledge,
        constraint=technical_constraint,
    )

    # Save
    file_list = await save_framework(dir_data=framework, output_dir=output_dir)
    logger.info(f"Output:\n{file_list}")


@app.command()
def startup(
    user_requirement_filename: str = typer.Argument(..., help="The filename of the user requirements."),
    actors_filename: str = typer.Argument(..., help="The filename of UML use case actors description."),
    acknowledge_filename: str = typer.Argument(..., help="External interfaces declarations."),
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

    asyncio.run(
        develop(ctx, user_requirement_filename, actors_filename, acknowledge_filename, constraint_filename, output_dir)
    )


if __name__ == "__main__":
    app()

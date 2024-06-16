#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional

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
from metagpt.const import ASSISTANT_ALIAS
from metagpt.context import Context
from metagpt.logs import ToolLogItem, log_tool_output, logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.cost_manager import CostManager


async def import_git_repo(url: str) -> Path:
    """
    Imports a project from a Git website and formats it to MetaGPT project format to enable incremental appending requirements.

    Args:
        url (str): The Git project URL, such as "https://github.com/geekan/MetaGPT.git".

    Returns:
        Path: The path of the formatted project.

    Example:
        # The Git project URL to input
        >>> git_url = "https://github.com/geekan/MetaGPT.git"

        # Import the Git repository and get the formatted project path
        >>> formatted_project_path = await import_git_repo(git_url)
        >>> print("Formatted project path:", formatted_project_path)
        /PATH/TO/THE/FORMMATTED/PROJECT
    """
    from metagpt.actions.import_repo import ImportRepo
    from metagpt.context import Context

    log_tool_output(
        output=[ToolLogItem(name=ASSISTANT_ALIAS, value=import_git_repo.__name__)], tool_name=import_git_repo.__name__
    )

    ctx = Context()
    action = ImportRepo(repo_path=url, context=ctx)
    await action.run()

    outputs = [ToolLogItem(name="MetaGPT Project", value=str(ctx.repo.workdir))]
    log_tool_output(output=outputs, tool_name=import_git_repo.__name__)

    return ctx.repo.workdir


async def extract_external_interfaces(acknowledge: str) -> str:
    """
    Extracts and compresses information about external system interfaces from a given acknowledgement text.

    Args:
        acknowledge (str): A natural text of acknowledgement containing details about external system interfaces.

    Returns:
        str: A compressed version of the information about external system interfaces.

    Example:
        >>> acknowledge = "## Interfaces\\n..."
        >>> external_interfaces = await extract_external_interfaces(acknowledge=acknowledge)
        >>> print(external_interfaces)
        ```json\n[\n{\n"id": 1,\n"inputs": {...
    """
    compress_acknowledge = CompressExternalInterfaces()
    return await compress_acknowledge.run(acknowledge=acknowledge)


@register_tool(tags=["system design", "write trd", "Write a TRD"])
async def write_trd(
    use_case_actors: str,
    user_requirements: str,
    acknowledge: str,
    investment: float = 10,
    context: Optional[Context] = None,
) -> (str, str):
    """
    Handles the writing of a Technical Requirements Document (TRD) based on user requirements.

    Args:
        user_requirements (str): The new/incremental user requirements.
        use_case_actors (str): Description of the actors involved in the use case.
        acknowledge (str): A natural text of acknowledgement containing details about external system interfaces.
        investment (float): Budget. Automatically stops optimizing TRD when the budget is overdrawn.
        context (Context, optional): The context configuration. Default is None.
    Returns:
        str: The newly created TRD.

    Example:
        >>> # Given a new user requirements, write out a new TRD.
        >>> user_requirements = "Write a 'snake game' TRD."
        >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
        >>> acknowledge = "## Interfaces\\n..."
        >>> investment = 10.0
        >>> trd = await write_trd(
        >>>     user_requirements=user_requirements,
        >>>     use_case_actors=use_case_actors,
        >>>     external_interfaces=external_interfaces,
        >>>     investment=investment,
        >>> )
        >>> print(trd)
        ## Technical Requirements Document\n ...
    """
    context = context or Context(cost_manager=CostManager(max_budget=investment))
    compress_acknowledge = CompressExternalInterfaces()
    external_interfaces = await compress_acknowledge.run(acknowledge=acknowledge)
    detect_interaction = DetectInteraction(context=context)
    w_trd = WriteTRD(context=context)
    evaluate_trd = EvaluateTRD(context=context)
    is_pass = False
    evaluation_conclusion = ""
    interaction_events = ""
    trd = ""
    while not is_pass and (context.cost_manager.total_cost < context.cost_manager.max_budget):
        interaction_events = await detect_interaction.run(
            user_requirements=user_requirements,
            use_case_actors=use_case_actors,
            legacy_interaction_events=interaction_events,
            evaluation_conclusion=evaluation_conclusion,
        )
        trd = await w_trd.run(
            user_requirements=user_requirements,
            use_case_actors=use_case_actors,
            available_external_interfaces=external_interfaces,
            evaluation_conclusion=evaluation_conclusion,
            interaction_events=interaction_events,
            previous_version_trd=trd,
        )
        evaluation = await evaluate_trd.run(
            user_requirements=user_requirements,
            use_case_actors=use_case_actors,
            trd=trd,
            interaction_events=interaction_events,
        )
        is_pass = evaluation.is_pass
        evaluation_conclusion = evaluation.conclusion

    return trd


@register_tool(tags=["system design", "write software framework", "Write a software framework based on a TRD"])
async def write_framework(
    use_case_actors: str,
    trd: str,
    acknowledge: str,
    additional_technical_requirements: str,
    output_dir: Optional[str] = "",
    investment: float = 10,
    context: Optional[Context] = None,
) -> str:
    """
    Run the action to generate a software framework based on the provided TRD and related information.

    Args:
        use_case_actors (str): Description of the use case actors involved.
        trd (str): Technical Requirements Document detailing the requirements.
        acknowledge (str): External acknowledgements or acknowledgements required.
        additional_technical_requirements (str): Any additional technical requirements.
        output_dir (str, optional): Path to save the software framework files. Default is en empty string.
        investment (float): Budget. Automatically stops optimizing TRD when the budget is overdrawn.
        context (Context, optional): The context configuration. Default is None.

    Returns:
        str: The generated software framework as a string of pathnames.

    Example:
        >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
        >>> trd = "## TRD\\n..."
        >>> acknowledge = "## Interfaces\\n..."
        >>> additional_technical_requirements = "Using Java language, ..."
        >>> investment = 10.0
        >>> framework = await write_framework(
        >>>    use_case_actors=use_case_actors,
        >>>    trd=trd,
        >>>    acknowledge=acknowledge,
        >>>    additional_technical_requirements=constraint,
        >>>    investment=investment,
        >>> )
        >>> print(framework)
        [{"path":"balabala", "filename":"...", ...
    """
    context = context or Context(cost_manager=CostManager(max_budget=investment))
    write_framework = WriteFramework(context=context)
    evaluate_framework = EvaluateFramework(context=context)
    is_pass = False
    framework = ""
    evaluation_conclusion = ""
    while not is_pass and (context.cost_manager.total_cost < context.cost_manager.max_budget):
        try:
            framework = await write_framework.run(
                use_case_actors=use_case_actors,
                trd=trd,
                acknowledge=acknowledge,
                legacy_output=framework,
                evaluation_conclusion=evaluation_conclusion,
                additional_technical_requirements=additional_technical_requirements,
            )
        except Exception as e:
            logger.info(f"{e}")
            break
        evaluation = await evaluate_framework.run(
            use_case_actors=use_case_actors,
            trd=trd,
            acknowledge=acknowledge,
            legacy_output=framework,
            additional_technical_requirements=additional_technical_requirements,
        )
        is_pass = evaluation.is_pass
        evaluation_conclusion = evaluation.conclusion

    file_list = await save_framework(dir_data=framework, output_dir=output_dir)
    logger.info(f"Output:\n{file_list}")
    return "\n".join(file_list)

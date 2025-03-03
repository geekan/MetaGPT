#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : evaluate_framework.py
@Desc    : The implementation of Chapter 2.1.8 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""

from metagpt.actions.requirement_analysis import EvaluateAction, EvaluationData
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import to_markdown_code_block


@register_tool(include_functions=["run"])
class EvaluateFramework(EvaluateAction):
    """WriteFramework deal with the following situations:
    1. Given a TRD and the software framework based on the TRD, evaluate the quality of the software framework.
    """

    async def run(
        self,
        *,
        use_case_actors: str,
        trd: str,
        acknowledge: str,
        legacy_output: str,
        additional_technical_requirements: str,
    ) -> EvaluationData:
        """
        Run the evaluation of the software framework based on the provided TRD and related parameters.

        Args:
            use_case_actors (str): A description of the actors involved in the use case.
            trd (str): The Technical Requirements Document (TRD) that outlines the requirements for the software framework.
            acknowledge (str): External acknowledgments or acknowledgments information related to the framework.
            legacy_output (str): The previous versions of software framework returned by `WriteFramework`.
            additional_technical_requirements (str): Additional technical requirements that need to be considered during evaluation.

        Returns:
            EvaluationData: An object containing the results of the evaluation.

        Example:
            >>> evaluate_framework = EvaluateFramework()
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> trd = "## TRD\\n..."
            >>> acknowledge = "## Interfaces\\n..."
            >>> framework = '{"path":"balabala", "filename":"...", ...'
            >>> constraint = "Using Java language, ..."
            >>> evaluation = await evaluate_framework.run(
            >>>     use_case_actors=use_case_actors,
            >>>     trd=trd,
            >>>     acknowledge=acknowledge,
            >>>     legacy_output=framework,
            >>>     additional_technical_requirements=constraint,
            >>> )
            >>> is_pass = evaluation.is_pass
            >>> print(is_pass)
            True
            >>> evaluation_conclusion = evaluation.conclusion
            >>> print(evaluation_conclusion)
            Balabala...
        """
        prompt = PROMPT.format(
            use_case_actors=use_case_actors,
            trd=to_markdown_code_block(val=trd),
            acknowledge=to_markdown_code_block(val=acknowledge),
            legacy_output=to_markdown_code_block(val=legacy_output),
            additional_technical_requirements=to_markdown_code_block(val=additional_technical_requirements),
        )
        return await self._vote(prompt)


PROMPT = """
## Actor, System, External System
{use_case_actors}

## Legacy TRD
{trd}

## Acknowledge
{acknowledge}

## Legacy Outputs
{legacy_output}

## Additional Technical Requirements
{additional_technical_requirements}

---
You are a tool that evaluates the quality of framework code based on the TRD content;
You need to refer to the content of the "Legacy TRD" section to check for any errors or omissions in the framework code found in "Legacy Outputs";
The content of "Actor, System, External System" provides an explanation of actors and systems that appear in UML Use Case diagram;
Information about the external system missing from the "Legacy TRD" can be found in the "Acknowledge" section;
Which interfaces defined in "Acknowledge" are used in the "Legacy TRD"?
Do not implement the interface in "Acknowledge" section until it is used in "Legacy TRD", you can check whether they are the same interface by looking at its ID or url;
Parts not mentioned in the "Legacy TRD" will be handled by other TRDs, therefore, processes not present in the "Legacy TRD" are considered ready;
"Additional Technical Requirements" specifies the additional technical requirements that the generated software framework code must meet;
Do the parameters of the interface of the external system used in the code comply with it's specifications in 'Acknowledge'?
Is there a lack of necessary configuration files?
Return a markdown JSON object with:
- an "issues" key containing a string list of natural text about the issues that need to addressed, found in the "Legacy Outputs" if any exits, each issue found must provide a detailed description and include reasons;
- a "conclusion" key containing the evaluation conclusion;
- a "misalignment" key containing the judgement detail of the natural text string list about the misalignment with "Legacy TRD";
- a "is_pass" key containing a true boolean value if there is not any issue in the "Legacy Outputs";
"""

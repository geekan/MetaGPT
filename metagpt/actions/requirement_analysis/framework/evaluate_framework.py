#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : evaluate_framework.py
@Desc    : The implementation of Chapter 2.1.8 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""

from metagpt.actions.requirement_analysis import EvaluateAction, EvaluationData
from metagpt.utils.common import to_markdown_code_block


class EvaluateFramework(EvaluateAction):
    async def run(
        self,
        *,
        use_case_actors: str,
        trd: str,
        acknowledge: str,
        legacy_output: str,
        additional_technical_requirements: str,
    ) -> EvaluationData:
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
Information missing from the "Legacy TRD" can be found in the "Acknowledge" section;
Parts not mentioned in the "Legacy TRD" will be handled by other TRDs, therefore, processes not present in the "Legacy TRD" are considered ready;
"Additional Technical Requirements" specifies the additional technical requirements that the generated software framework code must meet;
Return a markdown JSON object with:
- a "is_pass" key containing a true boolean value if there is not any issue in the "Legacy Outputs";
- an "issues" key containing a string list of natural text about the issues found in the "Legacy Outputs" if any, each issue found must provide a detailed description and include reasons;
- a "conclusion" key containing the evaluation conclusion;
- a "misalignment" key containing the judgement detail of the natural text string list about the misalignment with "Legacy TRD";
"""

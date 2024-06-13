#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : evaluate_trd.py
@Desc    : The implementation of Chapter 2.1.6~2.1.7 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""

from metagpt.actions.requirement_analysis import EvaluateAction, EvaluationData
from metagpt.utils.common import to_markdown_code_block


class EvaluateTRD(EvaluateAction):
    async def run(
        self,
        *,
        user_requirements: str,
        use_case_actors: str,
        trd: str,
        interaction_events: str = "",
        legacy_user_requirements_interaction_events: str = "",
        incremental_user_requirements_interaction_events: str = "",
    ) -> EvaluationData:
        prompt = PROMPT.format(
            use_case_actors=use_case_actors,
            user_requirements=to_markdown_code_block(val=user_requirements),
            trd=to_markdown_code_block(val=trd),
            legacy_user_requirements_interaction_events=legacy_user_requirements_interaction_events,
            incremental_user_requirements_interaction_events=incremental_user_requirements_interaction_events,
            interaction_events=interaction_events,
        )
        return await self._vote(prompt)


PROMPT = """
## Actor, System, External System
{use_case_actors}

## User Requirements
{user_requirements}

## TRD Design
{trd}

## Interaction Events
{legacy_user_requirements_interaction_events}
{incremental_user_requirements_interaction_events}
{interaction_events}

---
You are a tool to evaluate the TRD design.
"Actor, System, External System" provides the possible participants in interaction events;
"User Requirements" provides the original requirements description, any parts not mentioned in this description will be handled by other modules, so do not fabricate requirements;
"Interaction Events" provides some identified interaction events and the interacting participants based on the content of the "User Requirements";
"TRD Design" provides a comprehensive design of the implementation steps for the original requirements, incorporating the interaction events from "Interaction Events" and adding additional steps to connect the complete upstream and downstream data flows;
To integrate the complete upstream and downstream data flows, "TRD Design" allows for the inclusion of steps not present in the original requirements description, provided these steps do not contradict the content explicitly described in the "User Requirements";
Which interactions from "Interaction Events" correspond to which steps in "TRD Design"? Please provide reasons.
Which aspects of "TRD Design" and "Interaction Events" do not align with the descriptions in "User Requirements"? Please provide detailed descriptions and reasons.
If the descriptions in "User Requirements" are divided into multiple steps in "TRD Design" and "Interaction Events," it can be considered compliant with the descriptions in "User Requirements" as long as it does not conflict with them;
There is a possibility of missing details in the descriptions of "User Requirements". Any additional steps in "TRD Design" and "Interaction Events" are considered compliant with "User Requirements" as long as they do not conflict with the descriptions provided in "User Requirements".
Return a markdown JSON object with:
- a "is_pass" key containing a true boolean value if there is not any issue in the "TRD Design";
- an "issues" key containing a string list of natural text about the issues found in the "TRD Design" if any, each issue found must provide a detailed description and include reasons;
- a "conclusion" key containing the evaluation conclusion;
- a "correspondence_between" key containing the judgement detail of the natural text string list about the correspondence between "Interaction Events" and "TRD Design" steps;
- a "misalignment" key containing the judgement detail of the natural text string list about the misalignment with "User Requirements";
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : evaluate_trd.py
@Desc    : The implementation of Chapter 2.1.6~2.1.7 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""

from metagpt.actions.requirement_analysis import EvaluateAction, EvaluationData
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import to_markdown_code_block


@register_tool(include_functions=["run"])
class EvaluateTRD(EvaluateAction):
    """EvaluateTRD deal with the following situations:
    1. Given a TRD, evaluates the quality and returns a conclusion.
    """

    async def run(
        self,
        *,
        user_requirements: str,
        use_case_actors: str,
        trd: str,
        interaction_events: str,
        legacy_user_requirements_interaction_events: str = "",
    ) -> EvaluationData:
        """
        Evaluates the given TRD based on user requirements, use case actors, interaction events, and optionally external legacy interaction events.

        Args:
            user_requirements (str): The requirements provided by the user.
            use_case_actors (str): The actors involved in the use case.
            trd (str): The TRD (Technical Requirements Document) to be evaluated.
            interaction_events (str): The interaction events related to the user requirements and the TRD.
            legacy_user_requirements_interaction_events (str, optional): External legacy interaction events tied to the user requirements. Defaults to an empty string.

        Returns:
            EvaluationData: The conclusion of the TRD evaluation.

        Example:
            >>> evaluate_trd = EvaluateTRD()
            >>> user_requirements = "User requirements 1. ..."
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> trd = "## TRD\\n..."
            >>> interaction_events = "['interaction ...', ...]"
            >>> evaluation_conclusion = "Issues: ..."
            >>> legacy_user_requirements_interaction_events = ["user requirements 1. ...", ...]
            >>> evaluation = await evaluate_trd.run(
            >>>    user_requirements=user_requirements,
            >>>    use_case_actors=use_case_actors,
            >>>    trd=trd,
            >>>    interaction_events=interaction_events,
            >>>    legacy_user_requirements_interaction_events=str(legacy_user_requirements_interaction_events),
            >>> )
            >>> is_pass = evaluation.is_pass
            >>> print(is_pass)
            True
            >>> evaluation_conclusion = evaluation.conclusion
            >>> print(evaluation_conclusion)
            ## Conclustion\n balabalabala...

        """
        prompt = PROMPT.format(
            use_case_actors=use_case_actors,
            user_requirements=to_markdown_code_block(val=user_requirements),
            trd=to_markdown_code_block(val=trd),
            legacy_user_requirements_interaction_events=legacy_user_requirements_interaction_events,
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

## External Interaction Events
{legacy_user_requirements_interaction_events}

## Interaction Events
{legacy_user_requirements_interaction_events}
{interaction_events}

---
You are a tool to evaluate the TRD design.
"Actor, System, External System" provides the all possible participants in interaction events;
"User Requirements" provides the original requirements description, any parts not mentioned in this description will be handled by other modules, so do not fabricate requirements;
"External Interaction Events" is provided by an external module for your use, its content is also referred to "Interaction Events" section; The content in "External Interaction Events" can be determined to be problem-free;
"External Interaction Events" provides some identified interaction events and the interacting participants based on the part of the content of the "User Requirements";
"Interaction Events" provides some identified interaction events and the interacting participants based on the content of the "User Requirements";
"TRD Design" provides a comprehensive design of the implementation steps for the original requirements, incorporating the interaction events from "Interaction Events" and adding additional steps to connect the complete upstream and downstream data flows;
In order to integrate the full upstream and downstream data flow, the "TRD Design" allows for the inclusion of steps that do not appear in the original requirements description, but do not conflict with those explicitly described in the "User Requirements";
Which interactions from "Interaction Events" correspond to which steps in "TRD Design"? Please provide reasons.
Which aspects of "TRD Design" and "Interaction Events" do not align with the descriptions in "User Requirements"? Please provide detailed descriptions and reasons.
If the descriptions in "User Requirements" are divided into multiple steps in "TRD Design" and "Interaction Events," it can be considered compliant with the descriptions in "User Requirements" as long as it does not conflict with them;
There is a possibility of missing details in the descriptions of "User Requirements". Any additional steps in "TRD Design" and "Interaction Events" are considered compliant with "User Requirements" as long as they do not conflict with the descriptions provided in "User Requirements";
If there are interaction events with external systems in "TRD Design", you must explicitly specify the ID of the external interface to use for the interaction events, the input and output parameters of the used external interface must explictly match the input and output of the interaction event；
Does the sequence of steps in "Interaction Events" cause performance or cost issues? Please provide detailed descriptions and reasons;
If each step of "TRD Design" has input data, its input data is provided either by the output of the previous steps or by participants of "Actor, System, External System", and there should be no passive data;
Return a markdown JSON object with:
- an "issues" key containing a string list of natural text about the issues that need to be addressed, found in the "TRD Design" if any exist, each issue found must provide a detailed description and include reasons;
- a "conclusion" key containing the evaluation conclusion;
- a "correspondence_between" key containing the judgement detail of the natural text string list about the correspondence between "Interaction Events" and "TRD Design" steps;
- a "misalignment" key containing the judgement detail of the natural text string list about the misalignment with "User Requirements";
- a "is_pass" key containing a true boolean value if there is not any issue in the "TRD Design";
"""

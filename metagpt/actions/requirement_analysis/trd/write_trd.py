#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : write_trd.py
@Desc    : The implementation of Chapter 2.1.6~2.1.7 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import general_after_log, to_markdown_code_block


class WriteTRD(Action):
    async def run(
        self,
        *,
        user_requirements: str = "",
        use_case_actors: str,
        available_external_interfaces: str,
        legacy_trd: str = "",
        evaluation_conclusion: str = "",
        interaction_events: str = "",
        legacy_user_requirements: str = "",
        legacy_user_requirements_trd: str = "",
        legacy_user_requirements_interaction_events: str = "",
        incremental_user_requirements: str = "",
        previous_version_trd: str = "",
        incremental_user_requirements_interaction_events: str = "",
    ) -> str:
        if incremental_user_requirements:
            return await self._write_incremental_trd(
                use_case_actors=use_case_actors,
                legacy_user_requirements=legacy_user_requirements,
                available_external_interfaces=available_external_interfaces,
                legacy_user_requirements_trd=legacy_user_requirements_trd,
                legacy_user_requirements_interaction_events=legacy_user_requirements_interaction_events,
                incremental_user_requirements=incremental_user_requirements,
                previous_version_trd=previous_version_trd,
                evaluation_conclusion=evaluation_conclusion,
                incremental_user_requirements_interaction_events=incremental_user_requirements_interaction_events,
            )
        return await self._write_new_trd(
            use_case_actors=use_case_actors,
            original_user_requirement=user_requirements,
            available_external_interfaces=available_external_interfaces,
            legacy_trd=legacy_trd,
            evaluation_conclusion=evaluation_conclusion,
            interaction_events=interaction_events,
        )

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _write_new_trd(
        self,
        *,
        use_case_actors: str,
        original_user_requirement: str,
        available_external_interfaces: str,
        legacy_trd: str,
        evaluation_conclusion: str,
        interaction_events: str,
    ) -> str:
        prompt = NEW_PROMPT.format(
            use_case_actors=use_case_actors,
            original_user_requirement=to_markdown_code_block(val=original_user_requirement),
            available_external_interfaces=available_external_interfaces,
            legacy_trd=to_markdown_code_block(val=legacy_trd),
            evaluation_conclusion=evaluation_conclusion,
            interaction_events=interaction_events,
        )
        return await self.llm.aask(prompt)

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _write_incremental_trd(
        self,
        *,
        use_case_actors: str,
        legacy_user_requirements: str,
        available_external_interfaces: str,
        legacy_user_requirements_trd: str,
        legacy_user_requirements_interaction_events: str,
        incremental_user_requirements: str,
        previous_version_trd: str,
        evaluation_conclusion: str,
        incremental_user_requirements_interaction_events: str,
    ):
        prompt = INCREMENTAL_PROMPT.format(
            use_case_actors=use_case_actors,
            legacy_user_requirements=to_markdown_code_block(val=legacy_user_requirements),
            available_external_interfaces=available_external_interfaces,
            legacy_user_requirements_trd=to_markdown_code_block(val=legacy_user_requirements_trd),
            legacy_user_requirements_interaction_events=legacy_user_requirements_interaction_events,
            incremental_user_requirements=to_markdown_code_block(val=incremental_user_requirements),
            previous_version_trd=to_markdown_code_block(val=previous_version_trd),
            evaluation_conclusion=evaluation_conclusion,
            incremental_user_requirements_interaction_events=incremental_user_requirements_interaction_events,
        )
        return await self.llm.aask(prompt)


NEW_PROMPT = """
## Actor, System, External System
{use_case_actors}

## User Requirements
{original_user_requirement}

## Available External Interfaces
{available_external_interfaces}

## Legacy TRD
{legacy_trd}

## Evaluation Conclusion
{evaluation_conclusion}

## Interaction Events
{interaction_events}

---
You are a TRD generator.
The content of "Actor, System, External System" provides an explanation of actors and systems that appear in UML Use Case diagram;
The content of "Available External Interfaces" provides the candidate steps, along with the inputs and outputs of each step;
"User Requirements" provides the original requirements description, any parts not mentioned in this description will be handled by other modules, so do not fabricate requirements;
"Legacy TRD" provides the old version of the TRD based on the "User Requirements" and can serve as a reference for the new TRD;
"Evaluation Conclusion" provides a summary of the evaluation of the old TRD in the "Legacy TRD" and can serve as a reference for the new TRD;
"Interaction Events" provides some identified interaction events and the interacting participants based on the content of the "User Requirements";
1. What inputs and outputs are described in the "User Requirements"?
2. How many steps are needed to achieve the inputs and outputs described in the "User Requirements"? Which actors from the "Actor, System, External System" section are involved in each step? What are the inputs and outputs of each step? Where is this output used, for example, as input for which interface or where it is required in the requirements, etc.?
3. Output a complete Technical Requirements Document (TRD)：
  3.1. In the description, use the actor and system names defined in the "Actor, System, External System" section to describe the interactors;
  3.2. The content should include the original text of the requirements from "User Requirements";
  3.3. In the TRD, each step can involve a maximum of two participants. If there are more than two participants, the step needs to be further split;
  3.4. In the TRD, each step must include detailed descriptions, inputs, outputs, participants, initiator, and the rationale for the step's existence. The rationale should reference the original text to justify it, such as specifying which interface requires the output of this step as parameters or where in the requirements this step is mandated, etc.
"""

INCREMENTAL_PROMPT = """
## Actor, System, External System
{use_case_actors}

## Legacy User Requirements
{legacy_user_requirements}

## Available External Interfaces
{available_external_interfaces}

## The TRD of Legacy User Requirements
{legacy_user_requirements_trd}


## The Interaction Events of Legacy User Requirements
{legacy_user_requirements_interaction_events}

## Incremental Requirements
{incremental_user_requirements}

## Legacy TRD
{previous_version_trd}

## Evaluation Conclusion
{evaluation_conclusion}

## Interaction Events
{incremental_user_requirements_interaction_events}

---
You are a TRD generator.
The content of "Actor, System, External System" provides an explanation of actors and systems that appear in UML Use Case diagram;
The content of "Available External Interfaces" provides the candidate steps, along with the inputs and outputs of each step;
"Legacy User Requirements" provides the original requirements description handled by other modules for your use;
"The TRD of Legacy User Requirements" is the TRD generated by other modules based on the "Legacy User Requirements" for your use;
"The Interaction Events of Legacy User Requirements" is the interaction events list generated by other modules based on the "Legacy User Requirements" for your use;
"Incremental Requirements" provides the original requirements description that you need to address, any parts not mentioned in this description will be handled by other modules, so do not fabricate requirements;
The requirements in "Legacy User Requirements" combined with the "Incremental Requirements" form a complete set of requirements, therefore, you need to add the TRD portion of the "Incremental Requirements" to "The TRD of Legacy User Requirements", the added content must not conflict with the original content of "The TRD of Legacy User Requirements";
"Legacy TRD" provides the old version of the TRD you previously wrote based on the "Incremental Requirements" and can serve as a reference for the new TRD;
"Evaluation Conclusion" provides a summary of the evaluation of the old TRD you generated in the "Legacy TRD", and the identified issues can serve as a reference for the new TRD you create;
"Interaction Events" provides some identified interaction events and the interacting participants based on the content of the "Incremental Requirements";
1. What inputs and outputs are described in the "Incremental Requirements"？
2. How many steps are needed to achieve the inputs and outputs described in the "Incremental Requirements"? Which actors from the "Actor, System, External System" section are involved in each step? What are the inputs and outputs of each step? Where is this output used, for example, as input for which interface or where it is required in the requirements, etc.?
3. Output a complete Technical Requirements Document (TRD)：
  3.1. In the description, use the actor and system names defined in the "Actor, System, External System" section to describe the interactors;
  3.2. The content should include the original text of the requirements from "User Requirements";
  3.3. In the TRD, each step can involve a maximum of two participants. If there are more than two participants, the step needs to be further split;
  3.4. In the TRD, each step must include detailed descriptions, inputs, outputs, participants, initiator, and the rationale for the step's existence. The rationale should reference the original text to justify it, such as specifying which interface requires the output of this step as parameters or where in the requirements this step is mandated, etc.
    """

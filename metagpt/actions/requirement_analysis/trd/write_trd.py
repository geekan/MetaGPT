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
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import general_after_log, to_markdown_code_block


@register_tool(include_functions=["run"])
class WriteTRD(Action):
    """WriteTRD deal with the following situations:
    1. Given some new user requirements, write out a new TRD(Technical Requirements Document).
    2. Given some incremental user requirements, update the legacy TRD.
    """

    async def run(
        self,
        *,
        user_requirements: str = "",
        use_case_actors: str,
        available_external_interfaces: str,
        evaluation_conclusion: str = "",
        interaction_events: str,
        previous_version_trd: str = "",
        legacy_user_requirements: str = "",
        legacy_user_requirements_trd: str = "",
        legacy_user_requirements_interaction_events: str = "",
    ) -> str:
        """
        Handles the writing or updating of a Technical Requirements Document (TRD) based on user requirements.

        Args:
            user_requirements (str): The new/incremental user requirements.
            use_case_actors (str): Description of the actors involved in the use case.
            available_external_interfaces (str): List of available external interfaces.
            evaluation_conclusion (str, optional): The conclusion of the evaluation of the TRD written by you. Defaults to an empty string.
            interaction_events (str): The interaction events related to the user requirements that you are handling.
            previous_version_trd (str, optional): The previous version of the TRD written by you, for updating.
            legacy_user_requirements (str, optional): Existing user requirements handled by an external object for your use. Defaults to an empty string.
            legacy_user_requirements_trd (str, optional): The TRD associated with the existing user requirements handled by an external object for your use. Defaults to an empty string.
            legacy_user_requirements_interaction_events (str, optional): Interaction events related to the existing user requirements handled by an external object for your use. Defaults to an empty string.

        Returns:
            str: The newly created or updated TRD written by you.

        Example:
            >>> # Given a new user requirements, write out a new TRD.
            >>> user_requirements = "Write a 'snake game' TRD."
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> available_external_interfaces = "The available external interfaces returned by `CompressExternalInterfaces.run` are ..."
            >>> previous_version_trd = "TRD ..." # The last version of the TRD written out if there is.
            >>> evaluation_conclusion = "Conclusion ..." # The conclusion returned by `EvaluateTRD.run` if there is.
            >>> interaction_events = "Interaction ..." # The interaction events returned by `DetectInteraction.run`.
            >>> write_trd = WriteTRD()
            >>> new_version_trd = await write_trd.run(
            >>>     user_requirements=user_requirements,
            >>>     use_case_actors=use_case_actors,
            >>>     available_external_interfaces=available_external_interfaces,
            >>>     evaluation_conclusion=evaluation_conclusion,
            >>>     interaction_events=interaction_events,
            >>>     previous_version_trd=previous_version_trd,
            >>> )
            >>> print(new_version_trd)
            ## Technical Requirements Document\n ...

            >>> # Given an incremental requirements, update the legacy TRD.
            >>> legacy_user_requirements = ["User requirements 1. ...", "User requirements 2. ...", ...]
            >>> legacy_user_requirements_trd = "## Technical Requirements Document\\n ..." # The TRD before integrating more user requirements.
            >>> legacy_user_requirements_interaction_events = ["The interaction events list of user requirements 1 ...", "The interaction events list of user requiremnts 2 ...", ...]
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> available_external_interfaces = "The available external interfaces returned by `CompressExternalInterfaces.run` are ..."
            >>> increment_requirements = "The incremental user requirements are ..."
            >>> evaluation_conclusion = "Conclusion ..." # The conclusion returned by `EvaluateTRD.run` if there is.
            >>> previous_version_trd = "TRD ..." # The last version of the TRD written out if there is.
            >>> write_trd = WriteTRD()
            >>> new_version_trd = await write_trd.run(
            >>>     user_requirements=increment_requirements,
            >>>     use_case_actors=use_case_actors,
            >>>     available_external_interfaces=available_external_interfaces,
            >>>     evaluation_conclusion=evaluation_conclusion,
            >>>     interaction_events=interaction_events,
            >>>     previous_version_trd=previous_version_trd,
            >>>     legacy_user_requirements=str(legacy_user_requirements),
            >>>     legacy_user_requirements_trd=legacy_user_requirements_trd,
            >>>     legacy_user_requirements_interaction_events=str(legacy_user_requirements_interaction_events),
            >>> )
            >>> print(new_version_trd)
            ## Technical Requirements Document\n ...
        """
        if legacy_user_requirements:
            return await self._write_incremental_trd(
                use_case_actors=use_case_actors,
                legacy_user_requirements=legacy_user_requirements,
                available_external_interfaces=available_external_interfaces,
                legacy_user_requirements_trd=legacy_user_requirements_trd,
                legacy_user_requirements_interaction_events=legacy_user_requirements_interaction_events,
                incremental_user_requirements=user_requirements,
                previous_version_trd=previous_version_trd,
                evaluation_conclusion=evaluation_conclusion,
                incremental_user_requirements_interaction_events=interaction_events,
            )
        return await self._write_new_trd(
            use_case_actors=use_case_actors,
            original_user_requirement=user_requirements,
            available_external_interfaces=available_external_interfaces,
            legacy_trd=previous_version_trd,
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
  3.4. In the TRD, each step must include detailed descriptions, inputs, outputs, participants, initiator, and the rationale for the step's existence. The rationale should reference the original text to justify it, such as specifying which interface requires the output of this step as parameters or where in the requirements this step is mandated, etc.;
  3.5. In the TRD, if you need to call interfaces of external systems, you must explicitly specify the interface IDs of the external systems you want to call;
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : detect_interaction.py
@Desc    : The implementation of Chapter 2.1.6 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import general_after_log, to_markdown_code_block


@register_tool(include_functions=["run"])
class DetectInteraction(Action):
    """DetectInteraction deal with the following situations:
    1. Given a natural text of user requirements, it identifies the interaction events and the participants of those interactions from the original text.
    """

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def run(
        self,
        *,
        user_requirements: str,
        use_case_actors: str,
        legacy_interaction_events: str,
        evaluation_conclusion: str,
    ) -> str:
        """
        Identifies interaction events and participants from the user requirements.

        Args:
            user_requirements (str): A natural language text detailing the user's requirements.
            use_case_actors (str): A description of the actors involved in the use case.
            legacy_interaction_events (str): The previous version of the interaction events identified by you.
            evaluation_conclusion (str): The external evaluation conclusions regarding the interactions events identified by you.

        Returns:
            str: A string summarizing the identified interaction events and their participants.

        Example:
            >>> detect_interaction = DetectInteraction()
            >>> user_requirements = "User requirements 1. ..."
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> previous_version_interaction_events = "['interaction ...', ...]"
            >>> evaluation_conclusion = "Issues: ..."
            >>> interaction_events = await detect_interaction.run(
            >>>    user_requirements=user_requirements,
            >>>    use_case_actors=use_case_actors,
            >>>    legacy_interaction_events=previous_version_interaction_events,
            >>>    evaluation_conclusion=evaluation_conclusion,
            >>> )
            >>> print(interaction_events)
            "['interaction ...', ...]"
        """
        msg = PROMPT.format(
            use_case_actors=use_case_actors,
            original_user_requirements=to_markdown_code_block(val=user_requirements),
            previous_version_of_interaction_events=legacy_interaction_events,
            the_evaluation_conclusion_of_previous_version_of_trd=evaluation_conclusion,
        )
        return await self.llm.aask(msg=msg)


PROMPT = """
## Actor, System, External System
{use_case_actors}

## User Requirements
{original_user_requirements}

## Legacy Interaction Events
{previous_version_of_interaction_events}

## Evaluation Conclusion
{the_evaluation_conclusion_of_previous_version_of_trd}

---
You are a tool for capturing interaction events.
"Actor, System, External System" provides the possible participants of the interaction event;
"Legacy Interaction Events" is the contents of the interaction events that you output earlier;
Some descriptions in the "Evaluation Conclusion" relate to the content of "User Requirements", and these descriptions in the "Evaluation Conclusion" address some issues regarding the content of "Legacy Interaction Events";
You need to capture the interaction events occurring in the description within the content of "User Requirements" word-for-word, including:
1. Who is interacting with whom. An interaction event has a maximum of 2 participants. If there are multiple participants, it indicates that multiple events are combined into one event and should be further split;
2. When an interaction event occurs, who is the initiator? What data did the initiator enter?
3. What data does the interaction event ultimately return according to the "User Requirements"?

You can check the data flow described in the "User Requirements" to see if there are any missing interaction events;
Return a markdown JSON object list, each object of the list containing:
- a "name" key containing the name of the interaction event;
- a "participants" key containing a string list of the names of the two participants;
- a "initiator" key containing the name of the participant who initiate the interaction;
- a "input" key containing a natural text description about the input data;
"""

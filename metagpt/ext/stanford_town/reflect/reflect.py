#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Reflect function

import datetime
import time

from metagpt.ext.stanford_town.actions.run_reflect_action import (
    AgentChatPoignancy,
    AgentEventPoignancy,
    AgentEventTriple,
    AgentFocusPt,
    AgentInsightAndGuidance,
    AgentMemoryOnConvo,
    AgentPlanThoughtOnConvo,
)
from metagpt.ext.stanford_town.memory.retrieve import new_agent_retrieve
from metagpt.ext.stanford_town.utils.utils import get_embedding
from metagpt.logs import logger


async def generate_focal_points(role: "STRole", n: int = 3):
    nodes = [
        [i.last_accessed, i] for i in role.memory.event_list + role.memory.thought_list if "idle" not in i.embedding_key
    ]
    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for _, i in nodes]

    statements = ""
    for node in nodes[-1 * role.scratch.importance_ele_n :]:
        statements += node.embedding_key + "\n"
    run_focal_pt = AgentFocusPt()
    return await run_focal_pt.run(role, statements, n)


async def generate_insights_and_evidence(role: "STRole", nodes: list, n: int = 5):
    statements = ""
    for count, node in enumerate(nodes):
        statements += f"{str(count)}. {node.embedding_key}\n"
    run_insight_and_guidance = AgentInsightAndGuidance()
    ret = await run_insight_and_guidance.run(role, statements, n)

    logger.info(ret)

    try:
        for thought, evi_raw in ret.items():
            evidence_node_id = [nodes[i].memory_id for i in evi_raw]
            ret[thought] = evidence_node_id
        return ret
    except Exception as exp:
        logger.error(f"generate_insights_and_evidence error:{exp}")
        return {"this is blank": "node_1"}


async def generate_action_event_triple(act_desp: str, role: "STRole"):
    """TODO

    INPUT:
        act_desp: the description of the action (e.g., "sleeping")
        role: The Persona class instance
    OUTPUT:
        a string of emoji that translates action description.
    EXAMPLE OUTPUT:
        "🧈🍞"
    """
    run_event_triple = AgentEventTriple()
    result = await run_event_triple.run(act_desp, role)
    return result


async def generate_poig_score(role: "STRole", event_type: str, description: str):
    if "is idle" in description:
        return 1

    if event_type == "event" or event_type == "thought":
        run_event_poignancy = AgentEventPoignancy()
        return await run_event_poignancy.run(role, description)
    elif event_type == "chat":
        run_chat_poignancy = AgentChatPoignancy()
        return await run_chat_poignancy.run(role, role.scratch.act_description)


async def generate_planning_thought_on_convo(role: "STRole", all_utt: str):
    run_planning_on_convo = AgentPlanThoughtOnConvo()
    return await run_planning_on_convo.run(role, all_utt)


async def generate_memo_on_convo(role: "STRole", all_utt: str):
    run_memo_on_convo = AgentMemoryOnConvo()
    return await run_memo_on_convo.run(role, all_utt)


# Done
async def run_reflect(role: "STRole"):
    """
    Run the actual reflection. We generate the focal points, retrieve any
    relevant nodes, and generate thoughts and insights.

    INPUT:
        role: Current Persona object
    Output:
        None
    """
    # Reflection requires certain focal points. Generate that first.
    focal_points = await generate_focal_points(role, 3)
    # Retrieve the relevant Nodesobject for each of the focal points.
    # <retrieved> has keys of focal points, and values of the associated Nodes.
    retrieved = new_agent_retrieve(role, focal_points)

    # For each of the focal points, generate thoughts and save it in the
    # agent's memory.
    for focal_pt, nodes in retrieved.items():
        xx = [i.embedding_key for i in nodes]
        for xxx in xx:
            logger.info(f"Nodes retrieved for `{focal_pt}` are `{xxx}`.")

        thoughts = await generate_insights_and_evidence(role, nodes, 5)
        # 生成的是字典类型
        for thought, evidence in thoughts.items():
            created = role.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await generate_action_event_triple("(" + thought + ")", role)
            keywords = set([s, p, o])
            thought_poignancy = await generate_poig_score(role, "thought", thought)
            thought_embedding_pair = (thought, get_embedding(thought))

            role.memory.add_thought(
                created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, evidence
            )
            logger.info(f"add thought memory: {thought}, evidence: {evidence}")
            time.sleep(2)  # avoid Rate limit


def reflection_trigger(role: "STRole"):
    """
    Given the current role, determine whether the role should run a
    reflection.

    Our current implementation checks for whether the sum of the new importance
    measure has reached the set (hyper-parameter) threshold.

    INPUT:
        role: Current Persona object
    Output:
        True if we are running a new reflection.
        False otherwise.
    """
    logger.info(f"{role.scratch.name} role.scratch.importance_trigger_curr:: {role.scratch.importance_trigger_curr}"),

    if role.scratch.importance_trigger_curr <= 0 and [] != role.memory.event_list + role.memory.thought_list:
        return True
    return False


# Done
def reset_reflection_counter(role: "STRole"):
    """
    We reset the counters used for the reflection trigger.

    INPUT:
        role: Current Persona object
    Output:
        None
    """
    role_imt_max = role.scratch.importance_trigger_max
    role.scratch.importance_trigger_curr = role_imt_max
    role.scratch.importance_ele_n = 0


async def role_reflect(role: "STRole"):
    """
    The main reflection module for the role. We first check if the trigger
    conditions are met, and if so, run the reflection and reset any of the
    relevant counters.

    INPUT:
        role: Current Persona object
    Output:
        None
    """
    if reflection_trigger(role):
        await run_reflect(role)
        reset_reflection_counter(role)

    if role.scratch.chatting_end_time:
        # update 10 to it's real sec_per_step value
        if role.scratch.curr_time + datetime.timedelta(0, role.sec_per_step) == role.scratch.chatting_end_time:
            all_utt = ""
            if role.scratch.chat:
                for row in role.scratch.chat:
                    all_utt += f"{row[0]}: {row[1]}\n"

            last_chat = role.memory.get_last_chat(role.scratch.chatting_with)
            if last_chat:
                evidence = [last_chat.memory_id]
            else:
                logger.info(f"Role: {role.name} get_last_chat: {last_chat}")
                return

            planning_thought = await generate_planning_thought_on_convo(role, all_utt)
            planning_thought = f"For {role.scratch.name}'s planning: {planning_thought}"
            logger.info(f"Role: {role.name} planning_thought: {planning_thought}")

            created = role.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await generate_action_event_triple(planning_thought, role)
            keywords = set([s, p, o])
            thought_poignancy = await generate_poig_score(role, "thought", planning_thought)
            thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

            role.memory.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                planning_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )

            memo_thought = await generate_memo_on_convo(role, all_utt)
            memo_thought = f"{role.scratch.name} {memo_thought}"

            created = role.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await generate_action_event_triple(memo_thought, role)
            keywords = set([s, p, o])
            thought_poignancy = await generate_poig_score(role, "thought", memo_thought)
            thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

            role.memory.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                memo_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )

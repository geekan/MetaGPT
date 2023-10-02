#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Reflect function
import datetime
import random
import sys

from numpy import dot
from numpy.linalg import norm
from ..roles.st_role import STRole
from ..utils.utils import get_embedding
from metagpt.logs import logger
from ..actions.run_reflect_action import (
    AgentFocusPt, AgentInsightAndGuidance, AgentEventTriple,
    AgentEventPoignancy, AgentChatPoignancy, AgentPlanThoughtOnConvo,
    AgentMemoryOnConvo
)


def generate_focal_points(role: STRole, n=3):
    nodes = [
        [i.last_accessed, i] for i in
        role._rc.memory.event_list + role._rc.memory.thought_list
        if "idle" not in i.embedding_key
    ]
    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for _, i in nodes]

    statements = ""
    for node in nodes[-1 * role._rc.scratch.importance_ele_n:]:
        statements += node.embedding_key + "\n"
    run_focal_pt = AgentFocusPt()
    return run_focal_pt.run(role, statements, n)


def generate_insights_and_evidence(role, nodes, n=5):
    statements = ""
    for count, node in enumerate(nodes):
        statements += f'{str(count)}. {node.embedding_key}\n'
    run_insight_and_guidance = AgentInsightAndGuidance()
    ret = run_insight_and_guidance.run(role, statements, n)

    logger.info(ret)
    try:
        for thought, evi_raw in ret.items():
            evidence_node_id = [nodes[i].node_id for i in evi_raw]
            ret[thought] = evidence_node_id
        return ret
    except:
        return {"this is blank": "node_1"}


def generate_action_event_triple(act_desp, role):
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
    return AgentEventTriple(act_desp, role)


def generate_poig_score(role: STRole, event_type, description):
    if "is idle" in description:
        return 1

    if event_type == "event" or event_type == "thought":
        run_event_poignancy = AgentEventPoignancy()
        return run_event_poignancy.run(role, description)[0]
    elif event_type == "chat":
        run_chat_poignancy = AgentChatPoignancy()
        return run_chat_poignancy.run(role,
                                      role._rc.scratch.act_description)[0]


def generate_planning_thought_on_convo(role, all_utt):
    run_planning_on_convo = AgentPlanThoughtOnConvo()
    return run_planning_on_convo.run(role, all_utt)


def generate_memo_on_convo(role, all_utt):
    run_memo_on_convo = AgentMemoryOnConvo()
    return run_memo_on_convo.run(role, all_utt)


# Done
def run_reflect(role: STRole):
    """
    Run the actual reflection. We generate the focal points, retrieve any
    relevant nodes, and generate thoughts and insights.

    INPUT:
        role: Current Persona object
    Output:
        None
    """
    # Reflection requires certain focal points. Generate that first.
    focal_points = generate_focal_points(role, 3)
    # Retrieve the relevant Nodes object for each of the focal points.
    # <retrieved> has keys of focal points, and values of the associated Nodes.
    retrieved = role.retrieve(focal_points)

    # For each of the focal points, generate thoughts and save it in the
    # agent's memory.
    for focal_pt, nodes in retrieved.items():
        xx = [i.embedding_key for i in nodes]
        for xxx in xx: logger.info(xxx)

        thoughts = generate_insights_and_evidence(role, nodes, 5)
        # 生成的是字典类型
        for thought, evidence in thoughts.items():
            created = role.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(thought, role)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(role, "thought", thought)
            thought_embedding_pair = (thought, get_embedding(thought))

            role._rc.memory.add_thought(
                created, expiration, s, p, o, thought, keywords,
                thought_poignancy, thought_embedding_pair, evidence
            )


# Done
def reflection_trigger(role: STRole):
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
    logger.info(
        role._rc.scratch.name, "role.scratch.importance_trigger_curr::",
        role._rc.scratch.importance_trigger_curr
    )
    logger.info(role._rc.scratch.importance_trigger_max)

    if (role._rc.scratch.importance_trigger_curr <= 0 and
            [] != role._rc.memory.seq_event + role._rc.memory.seq_thought):
        return True
    return False


# Done
def reset_reflection_counter(role: STRole):
    """
    We reset the counters used for the reflection trigger.

    INPUT:
        role: Current Persona object
    Output:
        None
    """
    role_imt_max = role._rc.scratch.importance_trigger_max
    role._rc.scratch.importance_trigger_curr = role_imt_max
    role._rc.scratch.importance_ele_n = 0


# Question 1 chat函数
def reflect(role: STRole):
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
        run_reflect(role)
        reset_reflection_counter(role)

    if role._rc.scratch.chatting_end_time:
        if role._rc.scratch.curr_time + datetime.timedelta(0, 10) == role._rc.scratch.chatting_end_time:
            all_utt = ""
            if role._rc.scratch.chat:
                for row in role._rc.scratch.chat:
                    all_utt += f"{row[0]}: {row[1]}\n"

            # Question memory添加对话函数
            evidence = [role._rc.memory.get_last_chat(role._rc.scratch.chatting_with).memory_id]

            planning_thought = generate_planning_thought_on_convo(role, all_utt)
            planning_thought = f"For {role._rc.scratch.name}'s planning: {planning_thought}"

            created = role._rc.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(planning_thought, role)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(role, "thought", planning_thought)
            thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

            role._rc.memory.add_thought(
                created, expiration, s, p, o, planning_thought, keywords,
                thought_poignancy, thought_embedding_pair, evidence
            )

            memo_thought = generate_memo_on_convo(role, all_utt)
            memo_thought = f"{role._rc.scratch.name} {memo_thought}"

            created = role._rc.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(memo_thought, role)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(role, "thought", memo_thought)
            thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

            role._rc.memory.add_thought(
                created, expiration, s, p, o, memo_thought, keywords,
                thought_poignancy, thought_embedding_pair, evidence
            )

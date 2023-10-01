#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : reflect function
import sys

import datetime
import random

from numpy import dot
from numpy.linalg import norm
from ..roles.st_role import STRole
from ..utils.utils import get_embedding
from ..actions.run_reflect_action import AgentFocusPt,AgentInsightAndGuidance,AgentEventTriple,AgentEventPoignancy,AgentChatPoignancy,AgentPlanThoughtOnConvo,AgentMemoryOnConvo

def generate_focal_points(strole:STRole, n=3): 

    nodes = [[i.last_accessed, i]
              for i in strole._rc.memory.event_list + strole._rc.memory.thought_list
              if "idle" not in i.embedding_key]

    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for created, i in nodes]

    statements = ""
    for node in nodes[-1 * strole._rc.scratch.importance_ele_n:]: 
        statements += node.embedding_key + "\n"
    run_focal_pt = AgentFocusPt()
    # Question 1
    return run_focal_pt.run(strole, statements, n)


def generate_insights_and_evidence(strole, nodes, n=5): 

    statements = ""
    for count, node in enumerate(nodes): 
        statements += f'{str(count)}. {node.embedding_key}\n'
    run_insight_and_guidance = AgentInsightAndGuidance()
    ret = run_insight_and_guidance.run(strole, statements, n)

    print(ret)
    try: 

        for thought, evi_raw in ret.items(): 
            evidence_node_id = [nodes[i].node_id for i in evi_raw]
            ret[thought] = evidence_node_id
        return ret
    except: 
        return {"this is blank": "node_1"} 


def generate_action_event_triple(act_desp, strole): 
    """TODO 

    INPUT: 
        act_desp: the description of the action (e.g., "sleeping")
        strole: The Persona class instance
    OUTPUT: 
        a string of emoji that translates action description.
    EXAMPLE OUTPUT: 
        "🧈🍞"
    """
    run_event_triple = AgentEventTriple()
    return AgentEventTriple(act_desp, strole)


def generate_poig_score(strole:STRole, event_type, description): 

    if "is idle" in description: 
        return 1

    if event_type == "event" or event_type == "thought": 
        run_event_poignancy = AgentEventPoignancy()
        return run_event_poignancy.run(strole, description)[0]
    elif event_type == "chat": 
        run_chat_poignancy = AgentChatPoignancy()
        return run_chat_poignancy.run(strole, 
                               strole._rc.scratch.act_description)[0]


def generate_planning_thought_on_convo(strole, all_utt):
    run_planning_on_convo = AgentPlanThoughtOnConvo()
    return run_planning_on_convo.run(strole, all_utt)


def generate_memo_on_convo(strole, all_utt):
    run_memo_on_convo = AgentMemoryOnConvo()
    return run_memo_on_convo.run(strole, all_utt)



# Done
def run_reflect(strole:STRole):
    """
    Run the actual reflection. We generate the focal points, retrieve any 
    relevant nodes, and generate thoughts and insights. 

    INPUT: 
        strole: Current Persona object
    Output: 
        None
    """
    # Reflection requires certain focal points. Generate that first. 
    focal_points = generate_focal_points(strole, 3)
    # Retrieve the relevant Nodes object for each of the focal points. 
    # <retrieved> has keys of focal points, and values of the associated Nodes. 
    retrieved = strole.retrieve(focal_points) 

    # For each of the focal points, generate thoughts and save it in the 
    # agent's memory. 
    for focal_pt, nodes in retrieved.items(): 
        xx = [i.embedding_key for i in nodes]
        for xxx in xx: print(xxx)

        thoughts = generate_insights_and_evidence(strole, nodes, 5)
        # 生成的是字典类型
        for thought, evidence in thoughts.items(): 
            created = strole.scratch.curr_time
            expiration = strole.scratch.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(thought, strole)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(strole, "thought", thought)
            thought_embedding_pair = (thought, get_embedding(thought))

            strole._rc.memory.add_thought(created, expiration, s, p, o, 
                                      thought, keywords, thought_poignancy, 
                                      thought_embedding_pair, evidence)

# Done
def reflection_trigger(strole: STRole): 
    """
    Given the current strole, determine whether the strole should run a 
    reflection. 

    Our current implementation checks for whether the sum of the new importance
    measure has reached the set (hyper-parameter) threshold.

    INPUT: 
        strole: Current Persona object
    Output: 
        True if we are running a new reflection. 
        False otherwise. 
    """
    print(strole._rc.scratch.name, "strole.scratch.importance_trigger_curr::", strole._rc.scratch.importance_trigger_curr)
    print(strole._rc.scratch.importance_trigger_max)

    if (strole._rc.scratch.importance_trigger_curr <= 0 and 
        [] != strole._rc.memory.seq_event + strole._rc.memory.seq_thought): 
        return True 
    return False

# Done
def reset_reflection_counter(strole: STRole): 
    """
    We reset the counters used for the reflection trigger. 

    INPUT: 
        strole: Current Persona object
    Output: 
        None
    """
    strole_imt_max = strole._rc.scratch.importance_trigger_max
    strole._rc.scratch.importance_trigger_curr = strole_imt_max
    strole._rc.scratch.importance_ele_n = 0

# Question 1 chat函数
def reflect(strole: STRole):
    """
    The main reflection module for the strole. We first check if the trigger 
    conditions are met, and if so, run the reflection and reset any of the 
    relevant counters. 

    INPUT: 
        strole: Current Persona object
    Output: 
        None
    """
    if reflection_trigger(strole): 
        run_reflect(strole)
        reset_reflection_counter(strole)

    if strole._rc.scratch.chatting_end_time: 
        if strole._rc.scratch.curr_time + datetime.timedelta(0,10) == strole._rc.scratch.chatting_end_time: 
            all_utt = ""
            if strole._rc.scratch.chat: 
                for row in strole._rc.scratch.chat:  
                    all_utt += f"{row[0]}: {row[1]}\n"

            # Question memory添加对话函数
            evidence = [strole._rc.memory.get_last_chat(strole._rc.scratch.chatting_with).memory_id]

            planning_thought = generate_planning_thought_on_convo(strole, all_utt)
            planning_thought = f"For {strole._rc.scratch.name}'s planning: {planning_thought}"

            created = strole._rc.scratch.curr_time
            expiration = strole._rc.scratch.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(planning_thought, strole)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(strole, "thought", planning_thought)
            thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

            strole._rc.memory.add_thought(created, expiration, s, p, o, 
                                    planning_thought, keywords, thought_poignancy, 
                                    thought_embedding_pair, evidence)

            memo_thought = generate_memo_on_convo(strole, all_utt)
            memo_thought = f"{strole._rc.scratch.name} {memo_thought}"

            created = strole._rc.scratch.curr_time
            expiration = strole._rc.scratch.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(memo_thought, strole)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(strole, "thought", memo_thought)
            thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

            strole._rc.memory.add_thought(created, expiration, s, p, o, 
                                    memo_thought, keywords, thought_poignancy, 
                                    thought_embedding_pair, evidence)
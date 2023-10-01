#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Retrieve函数实现

import datetime
from typing import Union

from numpy import dot
from numpy.linalg import norm

from ..memory.agent_memory import AgentMemory, BasicMemory
from ..utils.utils import get_embedding


def agent_retrieve(agent_memory: AgentMemory, curr_time: datetime.datetime, memory_forget: float, query: str,
                   n: int = 30, topk: int = 4) -> list[BasicMemory]:
    """
    Retrieve需要集合Role使用,原因在于Role才具有AgentMemory,scratch
    逻辑:Role调用该函数,self._rc.AgentMemory,self._rc.scratch.curr_time,self._rc.scratch.memory_forget
    输入希望查询的内容与希望回顾的条数,返回TopK条高分记忆，即List[BasicMemory]

    Score_lists示例
    {
        "memory": memories[i],             BasicMemory类
        "importance": memories[i].poignancy
        "recency": 衰减因子计算结果
        "relevance": 搜索结果
    }
    """
    memories = agent_memory.storage
    sorted_memories = sorted(memories, key=lambda memory_node: memory_node.last_accessed_time, reverse=True)
    memories = sorted_memories[:n] if len(sorted_memories) >= n else sorted_memories

    score_list = []
    score_list = extract_importance(memories, score_list)
    score_list = extract_recency(curr_time, memory_forget, score_list)
    score_list = extract_relevance(query, score_list)
    score_list = normalize_score_floats(score_list, 0, 1)

    total_dict = {}
    gw = [1, 1, 1]  # 三个因素的权重,重要性,近因性,相关性
    for i in range(len(score_list)):
        total_score = (score_list[i]['importance'] * gw[0] +
                       score_list[i]['recency'] * gw[1] +
                       score_list[i]['relevance'] * gw[2]
                       )
        total_dict[score_list[i]['memory']] = total_score

    result = top_highest_x_values(total_dict, topk)

    return result


def top_highest_x_values(d, x):
    """
    输入字典，Topx
    返回以字典值排序，字典键组成的List[BasicMemory]
    """
    top_v = [item[0] for item in sorted(d.items(), key=lambda item: item[1], reverse=True)[:x]]
    return top_v


def extract_importance(memories, score_list):
    """
    抽取重要性
    """
    for i in range(len(memories)):
        score = {"memory": memories[i],
                 "importance": memories[i].poignancy
                 }
        score_list.append(score)
    return score_list


def extract_relevance(query, score_list):
    """
    抽取相关性
    """
    query_embedding = get_embedding(query)
    # 进行
    for i in range(len(score_list)):
        result = cos_sim(score_list[i]["memory"].embedding_key, query_embedding)
        score_list[i]['relevance'] = result

    return score_list


def extract_recency(curr_time, memory_forget, score_list):
    """
    抽取近因性，目前使用的现实世界过一天走一个衰减因子
    """
    for i in range(len(score_list)):
        day_count = (curr_time - score_list[i]['memory'].created).days
        score_list[i]['recency'] = memory_forget ** day_count
    return score_list


def cos_sim(a, b):
    """
    计算余弦相似度
    """
    return dot(a, b) / (norm(a) * norm(b))


def normalize_list_floats(single_list, target_min, target_max):
    """
    单个列表归一化
    """
    min_val = min(single_list)
    max_val = max(single_list)
    range_val = max_val - min_val

    if range_val == 0:
        for i in range(len(single_list)):
            single_list[i] = (target_max - target_min) / 2
    else:
        for i in range(len(single_list)):
            single_list[i] = ((single_list[i] - min_val) * (target_max - target_min)
                              / range_val + target_min)
    return single_list


def normalize_score_floats(score_list, target_min, target_max):
    """
    整体归一化
    """
    importance_list = []
    relevance_list = []
    recency_list = []

    for i in range(len(score_list)):
        importance_list.append(score_list[i]['importance'])
        relevance_list.append(score_list[i]['relevance'])
        recency_list.append(score_list[i]['recency'])

    # 进行归一化操作
    importance_list = normalize_list_floats(importance_list, target_min, target_max)
    relevance_list = normalize_list_floats(relevance_list, target_min, target_max)
    recency_list = normalize_list_floats(recency_list, target_min, target_max)

    for i in range(len(score_list)):
        score_list[i]['importance'] = importance_list[i]
        score_list[i]['relevance'] = relevance_list[i]
        score_list[i]['recency'] = recency_list[i]

    return score_list


def normalize_dict_floats(d: dict, target_min: Union[int, float], target_max: Union[int, float]) -> dict:
    """
    This function normalizes the float values of a given dictionary 'd' between
    a target minimum and maximum value. The normalization is done by scaling the
    values to the target range while maintaining the same relative proportions
    between the original values.

    INPUT:
      d: Dictionary. The input dictionary whose float values need to be
         normalized.
      target_min: Integer or float. The minimum value to which the original
                  values should be scaled.
      target_max: Integer or float. The maximum value to which the original
                  values should be scaled.
    OUTPUT:
      d: A new dictionary with the same keys as the input but with the float
         values normalized between the target_min and target_max.

    Example input:
      d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
      target_min = -5
      target_max = 5
    """
    min_val = min(val for val in d.values())
    max_val = max(val for val in d.values())
    range_val = max_val - min_val

    if range_val == 0:
        for key, val in d.items():
            d[key] = (target_max - target_min) / 2
    else:
        for key, val in d.items():
            d[key] = ((val - min_val) * (target_max - target_min)
                      / range_val + target_min)
    return d


def new_retrieve(role, focal_points, n_count=30):
    """
    Given the current role and focal points (focal points are events or
    thoughts for which we are retrieving), we retrieve a set of nodes for each
    of the focal points and return a dictionary.

    INPUT:
      role: The current role object whose memory we are retrieving.
      focal_points: A list of focal points (string description of the events or
                    thoughts that is the focus of current retrieval).
    OUTPUT:
      retrieved: A dictionary whose keys are a string focal point, and whose
                 values are a list of Node object in the agent's associative
                 memory.

    Example input:
      role = <role> object
      focal_points = ["How are you?", "Jane is swimming in the pond"]
    """
    # <retrieved> is the main dictionary that we are returning
    retrieved = dict()
    for focal_pt in focal_points:
        scratch = role._rc.scratch
        # Getting all nodes from the agent's memory (both thoughts and events) and
        # sorting them by the datetime of creation.
        # You could also imagine getting the raw conversation, but for now.
        nodes = [[i.last_accessed, i]
                 for i in role._rc.memory.event_list + role._rc.memory.thought_list
                 if "idle" not in i.embedding_key]
        nodes = sorted(nodes, key=lambda x: x[0])
        nodes = [i for created, i in nodes]

        # Calculating the component dictionaries and normalizing them.
        recency_out = extract_recency(role, nodes)  # TODO
        recency_out = normalize_dict_floats(recency_out, 0, 1)
        importance_out = extract_importance(role, nodes)
        importance_out = normalize_dict_floats(importance_out, 0, 1)
        relevance_out = extract_relevance(role, nodes, focal_pt)
        relevance_out = normalize_dict_floats(relevance_out, 0, 1)

        # Computing the final scores that combines the component values.
        # Note to self: test out different weights. [1, 1, 1] tends to work
        # decently, but in the future, these weights should likely be learned,
        # perhaps through an RL-like process.
        # gw = [1, 1, 1]
        # gw = [1, 2, 1]
        gw = [0.5, 3, 2]
        master_out = dict()
        for key in recency_out.keys():
            master_out[key] = (scratch.recency_w * recency_out[key] * gw[0]
                               + scratch.relevance_w * relevance_out[key] * gw[1]
                               + scratch.importance_w * importance_out[key] * gw[2])

        master_out = top_highest_x_values(master_out, len(master_out.keys()))
        for key, val in master_out.items():
            print(role._rc.memory.id_to_node[key].embedding_key, val)
            print(scratch.recency_w * recency_out[key] * 1,
                  scratch.relevance_w * relevance_out[key] * 1,
                  scratch.importance_w * importance_out[key] * 1)

        # Extracting the highest x values.
        # <master_out> has the key of node.id and value of float. Once we get the
        # highest x values, we want to translate the node.id into nodes and return
        # the list of nodes.
        master_out = top_highest_x_values(master_out, n_count)
        master_nodes = [role._rc.memory.id_to_node[key]
                        for key in list(master_out.keys())]

        for n in master_nodes:
            n.last_accessed = scratch.curr_time

        retrieved[focal_pt] = master_nodes

    return retrieved

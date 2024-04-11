#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Retrieve函数实现

import datetime

from numpy import dot
from numpy.linalg import norm

from metagpt.ext.stanford_town.memory.agent_memory import BasicMemory
from metagpt.ext.stanford_town.utils.utils import get_embedding


def agent_retrieve(
    agent_memory,
    curr_time: datetime.datetime,
    memory_forget: float,
    query: str,
    nodes: list[BasicMemory],
    topk: int = 4,
) -> list[BasicMemory]:
    """
    Retrieve需要集合Role使用,原因在于Role才具有AgentMemory,scratch
    逻辑:Role调用该函数,self.rc.AgentMemory,self.rc.scratch.curr_time,self.rc.scratch.memory_forget
    输入希望查询的内容与希望回顾的条数,返回TopK条高分记忆，即List[BasicMemory]

    Score_lists示例
    {
        "memory": memories[i],             BasicMemory类
        "importance": memories[i].poignancy
        "recency": 衰减因子计算结果
        "relevance": 搜索结果
    }
    """
    memories = nodes
    agent_memory_embedding = agent_memory.embeddings
    memories = sorted(memories, key=lambda memory_node: memory_node.last_accessed, reverse=True)

    score_list = []
    score_list = extract_importance(memories, score_list)
    score_list = extract_recency(curr_time, memory_forget, score_list)
    score_list = extract_relevance(agent_memory_embedding, query, score_list)
    score_list = normalize_score_floats(score_list, 0, 1)

    total_dict = {}
    gw = [1, 1, 1]  # 三个因素的权重,重要性,近因性,相关性,
    for i in range(len(score_list)):
        total_score = (
            score_list[i]["importance"] * gw[0] + score_list[i]["recency"] * gw[1] + score_list[i]["relevance"] * gw[2]
        )
        total_dict[score_list[i]["memory"].memory_id] = total_score

    result = top_highest_x_values(total_dict, topk)

    return result  # 返回的是一个BasicMemory列表


def new_agent_retrieve(role, focus_points: list, n_count=30) -> dict:
    """
    输入为role，关注点列表,返回记忆数量
    输出为字典，键为focus_point，值为对应的记忆列表
    """
    retrieved = dict()
    for focal_pt in focus_points:
        nodes = [
            [i.last_accessed, i]
            for i in role.memory.event_list + role.memory.thought_list
            if "idle" not in i.embedding_key
        ]
        nodes = sorted(nodes, key=lambda x: x[0])
        nodes = [i for created, i in nodes]
        results = agent_retrieve(
            role.memory, role.scratch.curr_time, role.scratch.recency_decay, focal_pt, nodes, n_count
        )
        final_result = []
        for n in results:
            for i in role.memory.storage:
                if i.memory_id == n:
                    i.last_accessed = role.scratch.curr_time
                    final_result.append(i)

        retrieved[focal_pt] = final_result

    return retrieved


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
        score = {"memory": memories[i], "importance": memories[i].poignancy}
        score_list.append(score)
    return score_list


def extract_relevance(agent_memory_embedding, query, score_list):
    """
    抽取相关性
    """
    query_embedding = get_embedding(query)
    # 进行
    for i in range(len(score_list)):
        node_embedding = agent_memory_embedding[score_list[i]["memory"].embedding_key]
        result = cos_sim(node_embedding, query_embedding)
        score_list[i]["relevance"] = result

    return score_list


def extract_recency(curr_time, memory_forget, score_list):
    """
    抽取近因性，目前使用的现实世界过一天走一个衰减因子
    """
    for i in range(len(score_list)):
        day_count = (curr_time - score_list[i]["memory"].created).days
        score_list[i]["recency"] = memory_forget**day_count
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
    if len(single_list) == 0:
        return []

    min_val = min(single_list)
    max_val = max(single_list)
    range_val = max_val - min_val

    if range_val == 0:
        for i in range(len(single_list)):
            single_list[i] = (target_max - target_min) / 2
    else:
        for i in range(len(single_list)):
            single_list[i] = (single_list[i] - min_val) * (target_max - target_min) / range_val + target_min
    return single_list


def normalize_score_floats(score_list, target_min, target_max):
    """
    整体归一化
    """
    importance_list = []
    relevance_list = []
    recency_list = []

    for i in range(len(score_list)):
        importance_list.append(score_list[i]["importance"])
        relevance_list.append(score_list[i]["relevance"])
        recency_list.append(score_list[i]["recency"])

    # 进行归一化操作
    importance_list = normalize_list_floats(importance_list, target_min, target_max)
    relevance_list = normalize_list_floats(relevance_list, target_min, target_max)
    recency_list = normalize_list_floats(recency_list, target_min, target_max)

    for i in range(len(score_list)):
        score_list[i]["importance"] = importance_list[i]
        score_list[i]["relevance"] = relevance_list[i]
        score_list[i]["recency"] = recency_list[i]

    return score_list

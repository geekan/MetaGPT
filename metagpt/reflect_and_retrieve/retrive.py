#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 实现GA中检索函数
# author: didi
# Date:9.25

from numpy import dot
from numpy.linalg import norm
from gpt_structure import embedding

# 实现三(2)合一搜索
def agent_retrive(agent,query,n,topk):
    # 将记忆列表按照Nodes[i].accessed_time排列，仅取前十个，如果不够10个就取现有的所有
    Nodes = agent.memories_list
    sorted_nodes = sorted(Nodes, key=lambda node: node.accessed_time,reverse=True)
    Nodes = sorted_nodes[:n] if len(sorted_nodes) >= n else sorted_nodes

    # 创建一个分数列表
    Score_list = []
    """
    {
        "memory":Nodes[i],
        "importance":Nodes[i].poignancy 
        "recency":衰减因子计算结果 
        "relevance":搜索结果
    }
    """
    Score_list = extract_importance(Nodes,Score_list)
    Score_list = extract_recency(Score_list) # 计算近因性函数还没有实现，目前都是1
    Score_list = extract_relevance(Score_list,query)

    Score_list = normalize_Socre_floats(Score_list,0,1)
    total_dict = {} 
    gw = [1,1,1] # 三个因素的权重,重要性，近因性，相关性
    for i in range(len(Score_list)):
        total_score = (Score_list[i]['importance']*gw[0] +
                       Score_list[i]['recency']*gw[1] +
                       Score_list[i]['relevance']*gw[2]
        )
        total_dict[Score_list[i]['memory'].description] = total_score        
    
    result = top_highest_x_values(total_dict,topk)

    return result

def top_highest_x_values(d, x):
  top_v = dict(sorted(d.items(), 
                      key=lambda item: item[1], 
                      reverse=True)[:x])
  return top_v
# 抽取重要性
def extract_importance(Nodes,Score_list):
    for i in range(len(Nodes)):
        Score = {"memory":Nodes[i],
                 "importance":Nodes[i].poignancy
                 }
        Score_list.append(Score)
    return Score_list

# 抽取相关性
def extract_relevance(Score_list,query):
    query_embedding = embedding(query)
    # 进行
    for i in range(len(Score_list)):
       result = cos_sim(Score_list[i]["memory"].embedding_key,query_embedding)
       Score_list[i]['relevance'] = result

    return Score_list

# 抽取近因性
def extract_recency(Score_list):
    for i in range(len(Score_list)):
       Score_list[i]['recency'] = 1
    return Score_list

# 计算余弦相似度
def cos_sim(a, b): 
  return dot(a, b)/(norm(a)*norm(b))

# 单个列表归一化
def normalize_List_floats(Single_list,target_min, target_max):
    min_val = min(Single_list)
    max_val = max(Single_list)
    range_val = max_val - min_val

    if range_val == 0: 
        for i in range(len(Single_list)):
           Single_list[i] = (target_max - target_min)/2
    else: 
        for i in range(len(Single_list)):
           Single_list[i] = ((Single_list[i] - min_val) * (target_max - target_min) 
                    / range_val + target_min)
    return Single_list

# 整体归一化
def normalize_Socre_floats(Score_list, target_min, target_max):

    importance_list = []
    relevance_list = []
    recency_list = []

    for i in range(len(Score_list)):
       importance_list.append(Score_list[i]['importance'])
       relevance_list.append(Score_list[i]['relevance'])
       recency_list.append(Score_list[i]['recency'])

    # 进行归一化操作
    importance_list = normalize_List_floats(importance_list,target_min, target_max)
    relevance_list = normalize_List_floats(relevance_list,target_min, target_max)
    recency_list =normalize_List_floats(recency_list,target_min, target_max)

    for i in range(len(Score_list)):
        Score_list[i]['importance'] = importance_list[i]
        Score_list[i]['relevance'] = relevance_list[i]
        Score_list[i]['recency'] = recency_list[i]
    
    return Score_list


   













#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Retrive函数实现

from numpy import dot
from numpy.linalg import norm
from datetime import datetime
from associative_memory import AgentMemory,MemoryBasic
from utils.utils import embedding_tools

def agent_retrive(agentmemory:AgentMemory, currtime:datetime, memory_forget:float, query:str, n:int= 30, topk:int=4) -> list[MemoryBasic]:
    """
    retrive需要集合Role使用,原因在于Role才具有AgentMemory,scratch
    逻辑:Role调用该函数,self._rc.AgentMemory,self._rc.scratch.currtime,self._rc.scratch.memory_forget
    输入希望查询的内容与希望回顾的条数,返回TopK条高分记忆，即List[MemoryBasic]

    Score_lists示例
    {
        "memory":memories[i],             MemoryBasic类
        "importance":memories[i].poignancy   
        "recency":衰减因子计算结果 
        "relevance":搜索结果
    }
    """
    memories = agentmemory.storage
    sorted_memories = sorted(memories, key=lambda memory_node: memory_node.last_accessed_time,reverse=True)
    memories = sorted_memories[:n] if len(sorted_memories) >= n else sorted_memories

    Score_list = []
    Score_list = extract_importance(memories,Score_list)
    Score_list = extract_recency(currtime,memory_forget,Score_list) 
    Score_list = extract_relevance(query,Score_list)
    Score_list = normalize_Socre_floats(Score_list,0,1)

    total_dict = {} 
    gw = [1,1,1] # 三个因素的权重,重要性，近因性，相关性
    for i in range(len(Score_list)):
        total_score = (Score_list[i]['importance']*gw[0] +
                       Score_list[i]['recency']*gw[1] +
                       Score_list[i]['relevance']*gw[2]
        )
        total_dict[Score_list[i]['memory']] = total_score      
    
    result = top_highest_x_values(total_dict,topk)

    return result

def top_highest_x_values(d, x):
    """
    输入字典，Topx
    返回以字典值排序，字典键组成的List[MemoryBasic]
    """
    top_v = [item[0] for item in sorted(d.items(),key=lambda item: item[1],reverse= True)[:x]]
    return top_v


def extract_importance(memories, Score_list):
    """
    抽取重要性
    """
    for i in range(len(memories)):
        Score = {"memory":memories[i],
                 "importance":memories[i].poignancy
                 }
        Score_list.append(Score)
    return Score_list

# 抽取相关性
def extract_relevance(query, Score_list):
    """
    抽取相关性
    """
    query_embedding = embedding_tools(query)
    # 进行
    for i in range(len(Score_list)):
       result = cos_sim(Score_list[i]["memory"].embedding_key,query_embedding)
       Score_list[i]['relevance'] = result

    return Score_list

# 抽取近因性
def extract_recency(currtime, memory_forget, Score_list):
    """
    抽取近因性，目前使用的现实世界过一天走一个衰减因子
    """
    for i in range(len(Score_list)):
       day_count = (currtime-Score_list[i]['memory'].created).days
       Score_list[i]['recency'] = memory_forget**day_count
    return Score_list

def cos_sim(a, b): 
  """
  计算余弦相似度
  """
  return dot(a, b)/(norm(a)*norm(b))

def normalize_List_floats(Single_list, target_min, target_max):
    """
    单个列表归一化
    """
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


def normalize_socre_floats(Score_list, target_min, target_max):
    """
    整体归一化
    """
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

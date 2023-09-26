#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 对应 GA中 concept node 实现 & AssociativeMemory 实现
# author: didi
# Date:9.24

from run_gpt import run_gpt_prompt_chat_poignancy, run_gpt_random_concept
from gpt_structure import embedding
from retrive import agent_retrive
import time
import json

# Meomry_basic 类


class Meomry_basic:
    def __init__(
            self, created_time, accessed_time,
            description,
            poignancy,
            embedding_key=None) -> None:
        """
        Initializes a basic memory object.

        Args:
            created_time (datetime): The time when the memory was created.
            accessed_time (datetime): The time when the memory was last accessed.
            description (str): The description of the memory.
            poignancy (int): The level of emotional intensity associated with the memory.
            embedding_key (Optional[str]): The embedding key for the memory (to avoid redundant vectorization).

        Returns:
            None
        """
        self.created_time = created_time      # 记忆创建时间
        self.accessed_time = accessed_time    # 记忆上次调用时间
        self.description = description        # 记忆描述
        self.poignancy = poignancy            # 记忆心酸程度
        if embedding_key is None:             # 记忆emmbeding key(避免重复向量化花钱)
            self.embedding_key = embedding(self.description)
        else:
            self.embedding_key = embedding_key

# Agent Memory 类


class Agent_memory(object):

    def __init__(self, name: str, iss: str,
                 memory_forget: float = 0.99,
                 memories_list: list[Meomry_basic] = [], memory_path: str = None) -> None:
        '''
        定义Agent,替换原有Agent使用，需要其他人根据需求补全功能。
        Attributes:
            name:agent name
            iss:agent iss（性格特征）
            memory_forget:agent 记忆遗忘速率（计算近因性）
            memories_list:agent 记忆JSON文件存储地址
            memory_path:记忆存储地址
        '''
        self.name = name                        # agent name
        self.iss = iss                          # agent iss（性格特征）
        self.memories_list = memories_list      # agent 记忆列表
        self.concept_forget = memory_forget     # agent 记忆遗忘速率（计算近因性）
        self.memory_path = memory_path          # agent 记忆JSON文件存储地址
        # agent 当前时间（现在使用的time.time()，等到环境搭好之后使用游戏内时间）
        self.curr_time = time.time()
        # 若给到memory_path 进行记忆初始化
        if memory_path:
            self.memories_list = self.memory_load(memory_path)

    def memory_save(self, PATH: str) -> None:
        '''
        将Memory存储在指定PATH的JSON文件中，命名为"{self.name}'s memory
        Args:
            PATH:str
        Return:
            None
        '''
        with open(PATH, 'w') as file:
            memory_data = [mem.__dict__ for mem in self.memories_list]
            json.dump(memory_data, file)

    def memory_load(self, PATH: str) -> list[Meomry_basic]:
        """
        将Memory从指定路径的JSON文件中Load出来,返回一个记忆列表;如果load失败，返回一个空列表。
        Args:
            PATH:str
        Return:
            List(Meomry_basic)
        """
        try:
            with open(PATH, 'r') as file:
                memory_data = json.load(file)
                self.memories_list = [Meomry_basic(
                    **mem) for mem in memory_data]
            return self.memories_list
        except OSError:
            return []


if __name__ == "__main__":
    # 例子，构建John Agent，实现retrive
    John_iss = """John Lin is a pharmacy shopkeeper at the Willow Market and Pharmacy who loves to help people. 
    He is always looking for ways to make the process of getting medication easier for his customers; 
    John Lin is living with his wife, Mei Lin, who is a college professor, and son, 
    Eddy Lin, who is a student studying music theory; John Lin loves his family very much; 
    John Lin has known the old couple next-door, 
    Sam Moore and Jennifer Moore, for a few years; 
    John Lin thinks Sam Moore is a kind and nice man; 
    John Lin knows his neighbor, Yuriko Yamamoto, well; 
    John Lin knows of his neighbors, Tamara Taylor and Carmen Ortiz, 
    but has not met them before; 
    John Lin and Tom Moreno are colleagues at The Willows Market and Pharmacy; 
    John Lin and Tom Moreno are friends and like to discuss local politics together; 
    John Lin knows the Moreno family somewhat well — the husband Tom Moreno and the wife Jane Moreno."""
    John = Agent_memory(
        "John", John_iss, memory_path="agent_memories/John_memory.json")

    for i in range(3):
        memory = run_gpt_random_concept()
        curr_time = time.time()
        poignancy = run_gpt_prompt_chat_poignancy(John, memory)
        M = Meomry_basic(curr_time, curr_time, memory, poignancy)
        John.memories_list.append(M)

    John.memory_save(John.memory_path)

    for i in range(len(John.memories_list)):
        print(f"John记忆为:{John.memories_list[i].description}")
        print(f"心酸程度为:{John.memories_list[i].poignancy}")
    query = "How has John's personal connection with his neighbors, such as the Moores and Yuriko, influenced his role as a pharmacy shopkeeper?"

    Top_v = agent_retrive(John, query, 10, 3)
    print(f"John的相关信息：{Top_v}")

    # John的相关信息：{'Had a friendly chat with Yuriko about her garden.': 2.4992317730827667, 'Helped Mrs. Moore carry groceries into her house.': 1.957656720441911, 'Discussed local politics with Tom Moreno.': 1.9458268038234035}

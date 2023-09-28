#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MemoryBasic,AgentMemory实现

from metagpt.memory.memory import Memory
from metagpt.schema import Message
import json
from datetime import datetime

class MemoryBasic(Message):

    def __init__(self, memory_id:str, memory_count:int, type_count:int, memory_type:str, depth:int, content:int,
                 creaetd:datetime, expiration:datetime,
                 subject:str, predicate:str, object:str,
                 embedding_key:str, poignancy:int, keywords:list, filling:list):
        """
        MemoryBasic继承于MG的Message类，其中content属性替代description属性
        Message类中对于Chat类型支持的非常好，对于Agent个体的Perceive,Reflection,Plan支持的并不多
        在Type设计上，我们延续GA的三个种类，但是对于Chat种类的对话进行特别设计（具体怎么设计还没想好）
        """
        super.__init__(content)
        """
        从父类中继承的属性
        content: str                                  # 记忆描述
        cause_by: Type["Action"] = field(default="")  # 触发动作，只在Type为chat时初始化
        cause_by 接受一个Action类，在此项目中，每个Agent需要有一个基础动作[Receive] 用于接受假对话Message；而每个Agent需要有独一无二的动作类，用以接受真对话Message
        """
        self.memory_id: str = memory_id               # 记忆ID
        self.memory_count: int = memory_count         # 第几个记忆，实际数值与Memory相等，但是类型为整数
        self.type_count: int = type_count             # 第几种记忆，类型为整数（具体不太理解如何生成的）
        self.memory_type: str = memory_type                         # 记忆类型，使用Field，包含 event,thought,chat三种类型
        self.depth:str  = depth                       # 记忆深度，类型为整数

        self.created: datetime = creaetd              # 创建时间
        self.expiration: datetime = expiration        # 记忆失效时间，默认为空（）
        self.last_accessed: datetime = creaetd        # 上一次调用的时间，初始化时候与self.created一致

        self.subject: str = subject                   # 主语，str类型                       
        self.predicate:str = predicate                # 谓语，str类型
        self.object:str = object                      # 宾语，str类型

        self.embedding_key: str = embedding_key       # 内容与self.content一致
        self.poignancy:int = poignancy                # importance值，整数类型
        self.keywords:list = keywords                 # keywords，列表
        self.filling:list = filling                   # None或者列表

class AgentMemory(Memory):
    """
    GA中主要存储三种JSON
    1. embedding.json (Dict embedding_key:embedding)
    2. Node.json (Dict Node_id:Node) 
    3. kw_strength.json 
    """
    def __init__(self, memory_saved:str):
        """
        AgentMemory类继承自Memory类，重写storage替代GA中id_to_node，一方面存储所有信息，一方面作为JSON转化
        index存储与不同Agent的chat信息
        @李嵩@张凯 这里的storage是List，你们需要写一个JSON转化器，将List修改为node.json一致的格式
        """
        super.__init__()
        self.storage: list[MemoryBasic] = []               # 重写Stroage，存储MemoryBasic所有节点
        self.event_list = []                               # 存储event记忆
        self.thought_list = []                             # 存储thought记忆
        
        self.event_keywords = dict()                       # 存储keywords
        self.thought_keywords = dict()                     
        self.chat_keywords = dict()

        self.strength_event_keywords = dict()              # 不知道具体作用，所以没有删除
        self.strength_thought_keywords = dict()           

        self.embeddings = json.load(open(memory_saved + "/embeddings.json")) # dict类型，load embedding.json
        self.memory_load()


    def memory_save(self):
        """
        将MemormyBasic类存储为Nodes.json形式。复现GA中的Kw Strength.json形式
        @张凯补充一个可调用的函数
        """
        pass

    def memory_load(self):
        """
        将GA的JSON解析，填充到AgentMemory类之中
        """
        pass

    def add(self, memory_basic: MemoryBasic):
        """
        Add a new message to storage, while updating the index
        重写add方法，修改原有的Message类为MemoryBasic类，并添加不同的记忆类型添加方式
        """
        if memory_basic in self.storage:
            return
        self.storage.append(memory_basic)
        if memory_basic.cause_by:
            self.index[memory_basic.cause_by].append(memory_basic)
            return 
        if memory_basic.type == "thought":
            self.thought_list.append(memory_basic)
            return
        if memory_basic.type == "event":
            self.event_list.append(memory_basic)  

    def add_chat(self):
        """
        调用add方法，初始化chat，在创建的时候就需要调用embeeding函数
        """
        pass

    def add_thought(self):
        """
        调用add方法，初始化thought
        """
        pass

    def add_event(self):
        """
        调用add方法，初始化event
        """
        pass

    def retrive(self,):
        """
        调用
        """
        pass

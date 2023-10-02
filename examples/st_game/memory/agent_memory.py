#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : BasicMemory,AgentMemory实现

from metagpt.memory.memory import Memory
from metagpt.schema import Message
import json
from datetime import datetime


class BasicMemory(Message):

    def __init__(self, memory_id: str, memory_count: int, type_count: int, memory_type: str, depth: int,
                 created: datetime, expiration: datetime,
                 subject: str, predicate: str, object: str,
                 content: str, embedding_key: str, poignancy: int, keywords: list, filling: list,
                 cause_by=""):
        """
        BasicMemory继承于MG的Message类，其中content属性替代description属性
        Message类中对于Chat类型支持的非常好，对于Agent个体的Perceive,Reflection,Plan支持的并不多
        在Type设计上，我们延续GA的三个种类，但是对于Chat种类的对话进行特别设计（具体怎么设计还没想好）
        """
        super().__init__(content, cause_by=cause_by)
        """
        从父类中继承的属性
        content: str                                  # 记忆描述
        cause_by: Type["Action"] = field(default="")  # 触发动作，只在Type为chat时初始化
        cause_by 接受一个Action类，在此项目中，每个Agent需要有一个基础动作[Receive] 用于接受假对话Message；
                而每个Agent需要有独一无二的动作类，用以接受真对话Message
        """
        self.memory_id: str = memory_id  # 记忆ID
        self.memory_count: int = memory_count  # 第几个记忆，实际数值与Memory相等
        self.type_count: int = type_count  # 第几种记忆，类型为整数（具体不太理解如何生成的）
        self.memory_type: str = memory_type  # 记忆类型，包含 event,thought,chat三种类型
        self.depth: str = depth  # 记忆深度，类型为整数

        self.created: datetime = created  # 创建时间
        self.expiration: datetime = expiration  # 记忆失效时间，默认为空（）
        self.last_accessed: datetime = self.created  # 上一次调用的时间，初始化时候与self.created一致

        self.subject: str = subject  # 主语
        self.predicate: str = predicate  # 谓语
        self.object: str = object  # 宾语

        self.embedding_key: str = embedding_key  # 内容与self.content一致
        self.poignancy: int = poignancy  # importance值
        self.keywords: list = keywords  # keywords
        self.filling: list = filling  # 装的与之相关联的memory_id的列表

    def summary(self):
        return (self.subject, self.predicate, self.object)

    def save_to_dict(self) -> dict:
        """
        将MemoryBasic类转化为字典，用于存储json文件
        这里需要注意，cause_by跟GA不兼容，所以需要做一个格式转换
        """
        memory_dict = dict()
        node_id = self.memory_id

        memory_dict[node_id] = dict()
        memory_dict[node_id]["node_count"] = self.memory_count
        memory_dict[node_id]["type_count"] = self.type_count
        memory_dict[node_id]["type"] = self.type
        memory_dict[node_id]["depth"] = self.depth

        memory_dict[node_id]["cmemory_dicteated"] = self.created.strftime('%Y-%m-%d %H:%M:%S')
        memory_dict[node_id]["expiration"] = None
        if self.expiration:
            memory_dict[node_id]["expiration"] = (self.expiration
                                                  .strftime('%Y-%m-%d %H:%M:%S'))

        memory_dict[node_id]["subject"] = self.subject
        memory_dict[node_id]["predicate"] = self.predicate
        memory_dict[node_id]["object"] = self.object

        memory_dict[node_id]["description"] = self.description
        memory_dict[node_id]["embedding_key"] = self.embedding_key
        memory_dict[node_id]["poignancy"] = self.poignancy
        memory_dict[node_id]["keywords"] = list(self.keywords)
        memory_dict[node_id]["filling"] = self.filling
        if self.cause_by:
            memory_dict[node_id]["cause_by"] = self.cause_by

        return memory_dict


class AgentMemory(Memory):
    """
    GA中主要存储三种JSON
    1. embedding.json (Dict embedding_key:embedding)
    2. Node.json (Dict Node_id:Node)
    3. kw_strength.json
    """

    def __init__(self, memory_saved: str):
        """
        AgentMemory类继承自Memory类，重写storage替代GA中id_to_node，一方面存储所有信息，一方面作为JSON转化
        index存储与不同Agent的chat信息
        @李嵩@张凯 这里的storage是List，你们需要写一个JSON转化器，将List修改为node.json一致的格式
        """
        super.__init__()
        self.id_to_node = dict()  # TODO jiayi add
        self.storage: list[BasicMemory] = []  # 重写Stroage，存储BasicMemory所有节点
        self.event_list = []  # 存储event记忆
        self.thought_list = []  # 存储thought记忆
        self.chat_list = []  # chat-related memory

        self.event_keywords = dict()  # 存储keywords
        self.thought_keywords = dict()
        self.chat_keywords = dict()

        self.kw_strength_event = dict()  # 关键词影响存储
        self.kw_strength_thought = dict()

        self.load(memory_saved)

    def save(self, memory_saved: str):
        """
        将MemormyBasic类存储为Nodes.json形式。复现GA中的Kw Strength.json形式
        这里添加一个路径即可
        """

        memory_json = dict()
        for i in range(len(self.storage)):
            memory_node = self.storage[i]
            memory_json.update(memory_node)
        with open(memory_saved + "/nodes.json", "w") as outfile:
            json.dump(memory_json, outfile)

        with open(memory_saved + "/embeddings.json", "w") as outfile:
            json.dump(self.embeddings, outfile)

        strength_json = dict()
        strength_json["kw_strength_event"] = self.kw_strength_event
        strength_json["kw_strength_thought"] = self.kw_strength_thought
        with open(memory_saved + "/kw_strength.json", "w") as outfile:
            json.dump(strength_json, outfile)

    def load(self, memory_saved: str):
        """
        将GA的JSON解析，填充到AgentMemory类之中
        """
        self.embeddings = json.load(open(memory_saved + "/embeddings.json"))
        memory_load = json.load(open(memory_saved + "/nodes.json"))
        for count in range(len(memory_load.keys())):
            node_id = f"node_{str(count + 1)}"
            node_details = memory_load[node_id]
            node_type = node_details["type"]
            created = datetime.datetime.strptime(node_details["created"],
                                                 '%Y-%m-%d %H:%M:%S')
            expiration = None
            if node_details["expiration"]:
                expiration = datetime.datetime.strptime(node_details["expiration"],
                                                        '%Y-%m-%d %H:%M:%S')

            if node_details["cause_by"]:
                cause_by = node_details["cause_by"]

            s = node_details["subject"]
            p = node_details["predicate"]
            o = node_details["object"]

            description = node_details["description"]
            embedding_pair = (node_details["embedding_key"],
                              self.embeddings[node_details["embedding_key"]])
            poignancy = node_details["poignancy"]
            keywords = set(node_details["keywords"])
            filling = node_details["filling"]

            if node_type == "event":
                self.add_event(created, expiration, s, p, o,
                               description, keywords, poignancy, embedding_pair, filling)
            elif node_type == "chat":
                self.add_chat(created, expiration, s, p, o,
                              description, keywords, poignancy, embedding_pair, filling, cause_by)
            elif node_type == "thought":
                self.add_thought(created, expiration, s, p, o,
                                 description, keywords, poignancy, embedding_pair, filling)

        strength_keywords_load = json.load(open(memory_saved + "/kw_strength.json"))
        if strength_keywords_load["kw_strength_event"]:
            self.kw_strength_event = strength_keywords_load["kw_strength_event"]
        if strength_keywords_load["kw_strength_thought"]:
            self.kw_strength_thought = strength_keywords_load["kw_strength_thought"]

    def add(self, memory_basic: BasicMemory):
        """
        Add a new message to storage, while updating the index
        重写add方法，修改原有的Message类为BasicMemory类，并添加不同的记忆类型添加方式
        """
        if memory_basic in self.storage:
            return
        self.storage.append(memory_basic)
        if memory_basic.cause_by:
            self.index[memory_basic.cause_by][0:0] = [memory_basic]
            return
        if memory_basic.type == "thought":
            self.thought_list[0:0] = [memory_basic]
            return
        if memory_basic.type == "event":
            self.event_list[0:0] = [memory_basic]

    def add_chat(self, created, expiration, s, p, o,
                 content, keywords, poignancy,
                 embedding_pair, filling,
                 cause_by):
        """
        调用add方法，初始化chat，在创建的时候就需要调用embeeding函数
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "chat"
        memory_id = f"memory_{str(memory_count)}"
        depth = 1

        memory_node = BasicMemory(memory_id, memory_count, type_count, memory_type, depth,
                                  created, expiration,
                                  s, p, o,
                                  content, embedding_pair[0],
                                  poignancy, keywords, filling,
                                  cause_by)

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.chat_keywords:
                self.chat_keywords[kw][0:0] = [memory_node]
            else:
                self.chat_keywords[kw] = [memory_node]

        self.add(memory_node)

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def add_thought(self, created, expiration, s, p, o,
                    content, keywords, poignancy,
                    embedding_pair, filling):
        """
        调用add方法，初始化thought
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "event"
        memory_id = f"memory_{str(memory_count)}"
        depth = 1

        try:
            if filling:
                depth_list = [memory_node.depth for memory_node in self.storage if memory_node.memory_id in filling]
                depth += max(depth_list)
        except Exception as exp:
            pass

        memory_node = BasicMemory(memory_id, memory_count, type_count, memory_type, depth,
                                  created, expiration,
                                  s, p, o,
                                  content, embedding_pair[0],
                                  poignancy, keywords, filling)

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.thought_keywords:
                self.thought_keywords[kw][0:0] = [memory_node]
            else:
                self.thought_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_thought:
                    self.kw_strength_thought[kw] += 1
                else:
                    self.kw_strength_thought[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def add_event(self, created, expiration, s, p, o,
                  content, keywords, poignancy,
                  embedding_pair, filling):
        """
        调用add方法，初始化event
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.event_list) + 1
        memory_type = "event"
        memory_id = f"memory_{str(memory_count)}"
        depth = 0

        if "(" in content:
            content = (" ".join(content.split()[:3])
                       + " "
                       + content.split("(")[-1][:-1])

        memory_node = BasicMemory(memory_id, memory_count, type_count, memory_type, depth,
                                  created, expiration,
                                  s, p, o,
                                  content, embedding_pair[0],
                                  poignancy, keywords, filling)

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.event_keywords:
                self.event_keywords[kw][0:0] = [memory_node]
            else:
                self.event_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_event:
                    self.kw_strength_event[kw] += 1
                else:
                    self.kw_strength_event[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def get_summarized_latest_events(self, retention):
        ret_set = set()
        for e_node in self.event_list[:retention]:
            ret_set.add(e_node.summary())
        return ret_set

    def get_last_chat(self, target_role_name: str) -> str:
        if target_role_name.lower() in self.chat_keywords:
            return self.chat_keywords[target_role_name.lower()][0]
        else:
            return False

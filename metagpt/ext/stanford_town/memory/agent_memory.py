#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : BasicMemory,AgentMemory实现

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import Field, field_serializer, model_validator

from metagpt.logs import logger
from metagpt.memory.memory import Memory
from metagpt.schema import Message
from metagpt.utils.common import read_json_file, write_json_file


class BasicMemory(Message):
    """
    BasicMemory继承于MG的Message类，其中content属性替代description属性
    Message类中对于Chat类型支持的非常好，对于Agent个体的Perceive,Reflection,Plan支持的并不多
    在Type设计上，我们延续GA的三个种类，但是对于Chat种类的对话进行特别设计（具体怎么设计还没想好）
    """

    memory_id: Optional[str] = Field(default=None)  # 记忆ID
    memory_count: int = -1  # 第几个记忆，实际数值与Memory相等
    type_count: int = -1  # 第几种记忆，类型为整数
    memory_type: Optional[str] = Field(default=None)  # 记忆类型，包含 event,thought,chat三种类型
    depth: int = -1  # 记忆深度，类型为整数
    created: Optional[datetime] = Field(default=None)  # 创建时间
    expiration: Optional[datetime] = Field(default=None)  # 记忆失效时间，默认为空（）
    last_accessed: Optional[datetime] = Field(default=None)  # 上一次调用的时间，初始化时候与self.created一致
    subject: Optional[str] = Field(default=None)  # 主语
    predicate: Optional[str] = Field(default=None)  # 谓语
    object: Optional[str] = Field(default=None)  # 宾语

    description: Optional[str] = Field(default=None)
    embedding_key: Optional[str] = Field(default=None)  # 内容与self.content一致
    poignancy: int = -1  # importance值
    keywords: list[str] = Field(default=[])  # keywords
    filling: list = Field(default=[])  # 装的与之相关联的memory_id的列表

    __hash__ = object.__hash__  # support hash in AgentMemory

    @model_validator(mode="before")
    @classmethod
    def check_values(cls, values):
        if "created" in values:
            values["last_accessed"] = values["created"]
        if "content" in values:
            values["description"] = values["content"]
        if "filling" in values:
            values["filling"] = values["filling"] or []
        return values

    @field_serializer("created", "expiration")
    def transform_time_field(self, time_field: Optional[datetime]) -> str:
        if time_field:
            time_field = time_field.strftime("%Y-%m-%d %H:%M:%S")
        return time_field

    def summary(self):
        return self.subject, self.predicate, self.object

    def save_to_dict(self) -> dict:
        """
        将MemoryBasic类转化为字典，用于存储json文件
        这里需要注意，cause_by跟GA不兼容，所以需要做一个格式转换
        """
        memory_dict = dict()
        node_id = self.memory_id
        basic_mem_obj = self.model_dump(
            include=[
                "node_count",
                "type_count",
                "type",
                "depth",
                "created",
                "expiration",
                "subject",
                "predicate",
                "object",
                "description",
                "embedding_key",
                "poignancy",
                "keywords",
                "filling",
                "cause_by",
            ]
        )

        memory_dict[node_id] = basic_mem_obj
        return memory_dict


class AgentMemory(Memory):
    """
    GA中主要存储三种JSON
    1. embedding.json (Dict embedding_key:embedding)
    2. Node.json (Dict Node_id:Node)
    3. kw_strength.json
    """

    storage: list[BasicMemory] = []  # 重写Storage，存储BasicMemory所有节点
    event_list: list[BasicMemory] = []  # 存储event记忆
    thought_list: list[BasicMemory] = []  # 存储thought记忆
    chat_list: list[BasicMemory] = []  # chat-related memory

    event_keywords: dict[str, list[BasicMemory]] = dict()  # 存储keywords
    thought_keywords: dict[str, list[BasicMemory]] = dict()
    chat_keywords: dict[str, list[BasicMemory]] = dict()

    kw_strength_event: dict[str, int] = dict()
    kw_strength_thought: dict[str, int] = dict()

    memory_saved: Optional[Path] = Field(default=None)
    embeddings: dict[str, list[float]] = dict()

    def set_mem_path(self, memory_saved: Path):
        self.memory_saved = memory_saved
        self.load(memory_saved)

    def save(self, memory_saved: Path):
        """
        将MemoryBasic类存储为Nodes.json形式。复现GA中的Kw Strength.json形式
        这里添加一个路径即可
        TODO 这里在存储时候进行倒序存储，之后需要验证（test_memory通过）
        """
        memory_json = dict()
        for i in range(len(self.storage)):
            memory_node = self.storage[len(self.storage) - i - 1]
            memory_node = memory_node.save_to_dict()
            memory_json.update(memory_node)
        write_json_file(memory_saved.joinpath("nodes.json"), memory_json)
        write_json_file(memory_saved.joinpath("embeddings.json"), self.embeddings)

        strength_json = dict()
        strength_json["kw_strength_event"] = self.kw_strength_event
        strength_json["kw_strength_thought"] = self.kw_strength_thought
        write_json_file(memory_saved.joinpath("kw_strength.json"), strength_json)

    def load(self, memory_saved: Path):
        """
        将GA的JSON解析，填充到AgentMemory类之中
        """
        self.embeddings = read_json_file(memory_saved.joinpath("embeddings.json"))
        memory_load = read_json_file(memory_saved.joinpath("nodes.json"))
        for count in range(len(memory_load.keys())):
            node_id = f"node_{str(count + 1)}"
            node_details = memory_load[node_id]
            node_type = node_details["type"]
            created = datetime.strptime(node_details["created"], "%Y-%m-%d %H:%M:%S")
            expiration = None
            if node_details["expiration"]:
                expiration = datetime.strptime(node_details["expiration"], "%Y-%m-%d %H:%M:%S")

            s = node_details["subject"]
            p = node_details["predicate"]
            o = node_details["object"]

            description = node_details["description"]
            embedding_pair = (node_details["embedding_key"], self.embeddings[node_details["embedding_key"]])
            poignancy = node_details["poignancy"]
            keywords = set(node_details["keywords"])
            filling = node_details["filling"]
            if node_type == "thought":
                self.add_thought(
                    created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling
                )
            if node_type == "event":
                self.add_event(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)
            if node_type == "chat":
                self.add_chat(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)

        strength_keywords_load = read_json_file(memory_saved.joinpath("kw_strength.json"))
        if strength_keywords_load["kw_strength_event"]:
            self.kw_strength_event = strength_keywords_load["kw_strength_event"]
        if strength_keywords_load["kw_strength_thought"]:
            self.kw_strength_thought = strength_keywords_load["kw_strength_thought"]

    def add(self, memory_basic: BasicMemory):
        """
        Add a new message to storage, while updating the index
        重写add方法，修改原有的Message类为BasicMemory类，并添加不同的记忆类型添加方式
        """
        if memory_basic.memory_id in self.storage:
            return
        self.storage.append(memory_basic)
        if memory_basic.memory_type == "chat":
            self.chat_list[0:0] = [memory_basic]
            return
        if memory_basic.memory_type == "thought":
            self.thought_list[0:0] = [memory_basic]
            return
        if memory_basic.memory_type == "event":
            self.event_list[0:0] = [memory_basic]
            return

    def add_chat(
        self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling, cause_by=""
    ):
        """
        调用add方法，初始化chat，在创建的时候就需要调用embedding函数
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "chat"
        memory_id = f"node_{str(memory_count)}"
        depth = 1

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
            cause_by=cause_by,
        )

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.chat_keywords:
                self.chat_keywords[kw][0:0] = [memory_node]
            else:
                self.chat_keywords[kw] = [memory_node]

        self.add(memory_node)

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def add_thought(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化thought
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "thought"
        memory_id = f"node_{str(memory_count)}"
        depth = 1

        try:
            if filling:
                depth_list = [memory_node.depth for memory_node in self.storage if memory_node.memory_id in filling]
                depth += max(depth_list)
        except Exception as exp:
            logger.warning(f"filling init occur {exp}")
            pass

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
        )

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

    def add_event(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化event
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.event_list) + 1
        memory_type = "event"
        memory_id = f"node_{str(memory_count)}"
        depth = 0

        if "(" in content:
            content = " ".join(content.split()[:3]) + " " + content.split("(")[-1][:-1]

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
        )

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

    def get_last_chat(self, target_role_name: str):
        if target_role_name.lower() in self.chat_keywords:
            return self.chat_keywords[target_role_name.lower()][0]
        else:
            return False

    def retrieve_relevant_thoughts(self, s_content: str, p_content: str, o_content: str) -> set:
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.thought_keywords:
                ret += self.thought_keywords[i.lower()]

        ret = set(ret)
        return ret

    def retrieve_relevant_events(self, s_content: str, p_content: str, o_content: str) -> set:
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.event_keywords:
                ret += self.event_keywords[i]

        ret = set(ret)
        return ret

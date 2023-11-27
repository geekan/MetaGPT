#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
"""
import asyncio
from typing import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

# from metagpt.document import Document
from metagpt.logs import logger
from metagpt.document import Repo
from metagpt.memory import Memory
from metagpt.roles import Role
from metagpt.schema import Message


class Environment(BaseModel):
    """
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    """

    roles: dict[str, Role] = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)
    history: str = Field(default='')
    repo: Repo = Field(default_factory=Repo)
    kv: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def add_role(self, role: Role):
        """增加一个在当前环境的角色
           Add a role in the current environment
        """
        role.set_env(self)
        self.roles[role.profile] = role

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的角色
            Add a batch of characters in the current environment
        """
        for role in roles:
            self.add_role(role)

    def publish_message(self, message: Message):
        """向当前环境发布信息
          Post information to the current environment
        """
        # self.message_queue.put(message)
        self.memory.add(message)
        self.history += f"\n{message}"

    def set_doc(self, content: str, filename: str):
        """向当前环境发布文档（包括代码）"""
        return self.repo.set(content, filename)

    def get_doc(self, filename: str):
        return self.repo.get(filename)

    def set(self, k: str, v: str):
        self.kv[k] = v

    def get(self, k: str):
        return self.kv.get(k, None)

    def load_existing_repo(self, path: Path, inc: bool):
        self.repo = Repo.from_path(path)
        logger.info(self.repo.eda())

        # Incremental mode: publish all docs to messages. Then roles can read the docs.
        if inc:
            docs = self.repo.get_text_documents()
            for doc in docs:
                msg = Message(content=doc.content)
                self.publish_message(msg)
                logger.info(f"Message from existing doc {doc.path}: {msg}")
            logger.info(f"Load {len(docs)} docs from existing repo.")
            raise NotImplementedError

    async def run(self, k=1):
        """处理一次所有信息的运行
        Process all Role runs at once
        """
        # while not self.message_queue.empty():
        # message = self.message_queue.get()
        # rsp = await self.manager.handle(message, self)
        # self.message_queue.put(rsp)
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                future = role.run()
                futures.append(future)

            await asyncio.gather(*futures)

    def get_roles(self) -> dict[str, Role]:
        """获得环境内的所有角色
           Process all Role runs at once
        """
        return self.roles

    def get_role(self, name: str) -> Role:
        """获得环境内的指定角色
           get all the environment roles
        """
        return self.roles.get(name, None)

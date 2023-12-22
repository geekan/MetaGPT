#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:00
@Author  : alexanderwu
@File    : base_chatbot.py
@Modified By: mashenquan, 2023/11/21. Add `timeout`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseChatbot(ABC):
    """Abstract GPT class"""

    mode: str = "API"
    use_system_prompt: bool = True

    @abstractmethod
    def ask(self, msg: str, timeout=3) -> str:
        """Ask GPT a question and get an answer"""

    @abstractmethod
    def ask_batch(self, msgs: list, timeout=3) -> str:
        """Ask GPT multiple questions and get a series of answers"""

    @abstractmethod
    def ask_code(self, msgs: list, timeout=3) -> str:
        """Ask GPT multiple questions and get a piece of code"""

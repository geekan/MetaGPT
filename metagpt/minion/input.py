#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : brain.py
"""

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EnsembleStrategyType(Enum):
    EARLY_STOP = "early_stop"
    ESTIMATE = "estimate"  # estimate which one is better
    VOTE = "vote"  # vote which one is better


class QuestionType(Enum):
    BLANK_FILLING_QUESTION = "blank filling question"
    TRUE_FALSE_QUESTION = "true-false question"
    MULTIPLE_CHOICE_QUESTION = "multiple-choice question"


class Input(BaseModel):
    long_context: str = Field(default="")
    short_context: str = ""  # abstract/summarized version
    query: str = ""
    query_type: str = "question"  # question or requirement
    guidance: str = ""
    constraint: str = ""  # question or requirement
    instruction: str = ""  # instruction for each step, different step can have different instruction
    complexity: str = ""  # low,medium,high
    query_range: str = ""  # short range query, or multiple step range like writing a very long novel
    # plan:str = "" # current plan
    score_func: Any = None

    answer: str = ""  # the extracted final answer
    answer_raw: str = ""  # the complete answer with cot thought

    question_type: str = ""  # a query sub type that determines the answer protocol
    answer_protocol: str = ""

    # metadata
    query_time: Any = None
    processed_minions: int = 0  # how many minions processed this
    metadata: dict = {}
    info: dict = {}
    route: Optional[str] = ""  # a tempory solution for routing
    num_trials: int = 1  # how much times downstream node runs
    ensemble_strategy: str = EnsembleStrategyType.EARLY_STOP

    run_id: str = Field(default_factory=uuid.uuid4)

    @property
    def context(self):
        return self.long_context

    @context.setter
    def context(self, context):
        self.long_context = context

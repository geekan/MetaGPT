#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ActionOp(Enum):
    TAP = "tap"
    LONG_PRESS = "long_press"
    TEXT = "text"
    SWIPE = "swipe"
    VERTICAL_SWIPE = "v_swipe"
    HORIZONTAL_SWIPE = "h_swipe"
    GRID = "grid"
    STOP = "stop"


class SwipeOp(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class Decision(Enum):
    BACK = "BACK"
    INEFFECTIVE = "INEFFECTIVE"
    CONTINUE = "CONTINUE"
    SUCCESS = "SUCCESS"

    @classmethod
    def values(cls):
        return [item.value for item in cls]


class AndroidElement(BaseModel):
    """UI Element"""

    uid: str = Field(default="")
    bbox: tuple[tuple[int, int], tuple[int, int]] = Field(default={})
    attrib: str = Field(default="")


class OpLogItem(BaseModel):
    """log content for self-learn or task act"""

    step: int = Field(default=0)
    prompt: str = Field(default="")
    image: str = Field(default="")
    response: str = Field(default="")


class ReflectLogItem(BaseModel):
    """log content for self-learn-reflect"""

    step: int = Field(default=0)
    prompt: str = Field(default="")
    image_before: str = Field(default="")
    image_after: str = Field(default="")
    response: str = Field(default="")


class RecordLogItem(BaseModel):
    """log content for record parse, same as ReflectLogItem"""

    step: int = Field(default=0)
    prompt: str = Field(default="")
    image_before: str = Field(default="")
    image_after: str = Field(default="")
    response: str = Field(default="")


class DocContent(BaseModel):
    tap: str = Field(default="")
    text: str = Field(default="")
    v_swipe: str = Field(default="")
    h_swipe: str = Field(default="")
    long_press: str = Field(default="")


# start =================== define different Action Op and its params =============
class RunState(Enum):
    """run state"""

    SUCCESS = "success"
    FINISH = "finish"
    FAIL = "fail"


class BaseOpParam(BaseModel):
    act_name: str = Field(default="", validate_default=True)
    last_act: str = Field(default="None")
    param_state: RunState = Field(default=RunState.SUCCESS, description="return state when extract params")


class TapOpParam(BaseOpParam):
    area: int = Field(default=-1)


class TextOpParam(BaseOpParam):
    input_str: str = Field(default="")


class LongPressOpParam(BaseOpParam):
    area: int = Field(default=-1)


# Modify This SwipeOp to SwipeOpParam, Need better name
class SwipeOpParam(BaseOpParam):
    area: int = Field(default=-1)
    swipe_orient: str = Field(default="up")
    dist: str = Field(default="")


class GridOpParam(BaseOpParam):
    act_name: str = Field(default="")


class BaseGridOpParam(BaseOpParam):
    @field_validator("act_name", mode="before")
    @classmethod
    def check_act_name(cls, act_name: str) -> str:
        return f"{act_name}_grid"


class TapGridOpParam(BaseGridOpParam):
    area: int = Field(default=-1)
    subarea: str = Field(default="")


class LongPressGridOpParam(BaseGridOpParam):
    area: int = Field(default=-1)
    subarea: str = Field(default="")


class SwipeGridOpParam(BaseGridOpParam):
    start_area: int = Field(default=-1)
    start_subarea: str = Field(default="")
    end_area: int = Field(default=-1)
    end_subarea: str = Field(default="")


# end =================== define different Action Op and its params =============


class ReflectOp(BaseModel):
    decision: str = ""
    thought: str = ""
    documentation: str = ""
    param_state: RunState = RunState.SUCCESS


class AndroidActionOutput(BaseModel):
    data: dict = Field(default=dict())
    action_state: RunState = Field(default=RunState.SUCCESS)

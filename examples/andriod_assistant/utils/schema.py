#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from pydantic import Field, BaseModel


class AndroidElement(BaseModel):
    """UI Element"""
    uid: str = Field(default="")
    bbox: tuple[tuple[int, int]] = Field(default={})
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


class DocContent(BaseModel):
    tap: str = Field(default="")
    text: str = Field(default="")
    v_swipe: str = Field(default="")
    h_swipe: str = Field(default="")
    long_press: str = Field(default="")



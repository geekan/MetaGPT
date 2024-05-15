#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect


async def get_human_input(prompt: str = ""):
    """interface for getting human input, can be set to get input from different sources with set_human_input_func"""
    if inspect.iscoroutinefunction(_get_human_input):
        return await _get_human_input(prompt)
    else:
        return _get_human_input(prompt)


def set_human_input_func(func):
    global _get_human_input
    _get_human_input = func


_get_human_input = input  # get human input from console by default

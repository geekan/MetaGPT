#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : __init__.py
@Desc    : The implementation of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""


from metagpt.actions.requirement_analysis.trd.detect_interaction import DetectInteraction
from metagpt.actions.requirement_analysis.trd.evaluate_trd import EvaluateTRD
from metagpt.actions.requirement_analysis.trd.write_trd import WriteTRD
from metagpt.actions.requirement_analysis.trd.compress_external_interfaces import CompressExternalInterfaces

__all__ = [CompressExternalInterfaces, DetectInteraction, WriteTRD, EvaluateTRD]

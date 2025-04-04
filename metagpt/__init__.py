#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/4/24 22:26
# @Author  : alexanderwu
# @File    : __init__.py

from metagpt import _compat as _  # noqa: F401
from metagpt import provider  # noqa: F401

# Import all providers to ensure they are registered
from metagpt.provider import *  # noqa: F403

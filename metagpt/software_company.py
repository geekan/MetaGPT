#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
from metagpt.team import Team as SoftwareCompany

import warnings
warnings.warn("metagpt.software_company is deprecated and will be removed in the future"
              "Please use metagpt.team instead. SoftwareCompany class is now named as Team.",
              DeprecationWarning, 2)

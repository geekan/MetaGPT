#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:32
# @Author  : lidanyang
# @File    : __init__.py
# @Desc    :
from metagpt.tools.libs import (data_preprocess, email_login, feature_engineering, gpt_v_generator, sd_engine,
                                web_scraping)

_ = (
    data_preprocess,
    feature_engineering,
    sd_engine,
    gpt_v_generator,
    web_scraping,
    email_login,
)  # Avoid pre-commit error

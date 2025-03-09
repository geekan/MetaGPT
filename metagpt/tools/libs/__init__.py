#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:32
# @Author  : lidanyang
# @File    : __init__.py
# @Desc    :
from metagpt.tools.libs import (
    data_preprocess,
    feature_engineering,
    sd_engine,
    gpt_v_generator,
    web_scraping,
    # email_login,
    terminal,
    editor,
    browser,
    deployer,
    git,
)
from metagpt.tools.libs.env import get_env, set_get_env_entry, default_get_env, get_env_description, get_env_default

_ = (
    data_preprocess,
    feature_engineering,
    sd_engine,
    gpt_v_generator,
    web_scraping,
    # email_login,
    terminal,
    editor,
    browser,
    deployer,
    git,
    get_env,
    get_env_default,
    get_env_description,
    set_get_env_entry,
    default_get_env,
)  # Avoid pre-commit error

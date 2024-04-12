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
    email_login,
    terminal,
    file_manager,
    browser,
    deployer,
)
from metagpt.tools.libs.software_development import (
    write_prd,
    write_design,
    write_project_plan,
    write_codes,
    run_qa_test,
    fix_bug,
    git_archive,
)

_ = (
    data_preprocess,
    feature_engineering,
    sd_engine,
    gpt_v_generator,
    web_scraping,
    email_login,
    write_prd,
    write_design,
    write_project_plan,
    write_codes,
    run_qa_test,
    fix_bug,
    git_archive,
    terminal,
    file_manager,
    browser,
    deployer,
)  # Avoid pre-commit error

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : metagpt_openapi_svc.py
@Desc    : MetaGPT OpenAPI REST API service
"""
from pathlib import Path
import sys
import connexion
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # fix-bug: No module named 'metagpt'
from metagpt.utils.common import initalize_enviroment

if __name__ == "__main__":
    initalize_enviroment()

    app = connexion.AioHttpApp(__name__, specification_dir='../../spec/')
    app.add_api("metagpt_openapi.yaml")
    app.run(port=8080)

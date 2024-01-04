#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/2 21:00
@Author  : alexanderwu
@File    : test_document.py
"""
from metagpt.config2 import config
from metagpt.document import Repo
from metagpt.logs import logger


def set_existing_repo(path):
    repo1 = Repo.from_path(path)
    repo1.set("doc/wtf_file.md", "wtf content")
    repo1.set("code/wtf_file.py", "def hello():\n    print('hello')")
    logger.info(repo1)  # check doc


def load_existing_repo(path):
    repo = Repo.from_path(path)
    logger.info(repo)
    logger.info(repo.eda())

    assert repo
    assert repo.get("doc/wtf_file.md").content == "wtf content"
    assert repo.get("code/wtf_file.py").content == "def hello():\n    print('hello')"


def test_repo_set_load():
    repo_path = config.workspace.path / "test_repo"
    set_existing_repo(repo_path)
    load_existing_repo(repo_path)

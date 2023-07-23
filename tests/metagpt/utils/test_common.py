#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:19
@Author  : alexanderwu
@File    : test_common.py
"""

import os

import pytest

from metagpt.const import get_project_root


class TestGetProjectRoot:
    def change_etc_dir(self):
        # current_directory = Path.cwd()
        abs_root = '/etc'
        os.chdir(abs_root)

    def test_get_project_root(self):
        project_root = get_project_root()
        assert project_root.name == 'metagpt'

    def test_get_root_exception(self):
        with pytest.raises(Exception) as exc_info:
            self.change_etc_dir()
            get_project_root()
        assert str(exc_info.value) == "Project root not found."

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/31 15:00
@Author  : chao.lan
@File    : test_source_control.py
"""
import os
import re
import shutil
import pytest
import subprocess
from metagpt.const import TMP
from metagpt.tools.source_control import GitControl

workspace = TMP / "test_source_control"

def test_init_repo():
    TMP.mkdir(exist_ok=True)
    git_repo = GitControl(workspace)
    os.chdir(workspace)
    git_status = subprocess.run(["git", "status"], capture_output=True)
    assert git_status.returncode == 0

def test_add_file():
    os.chdir(workspace)
    git_repo = GitControl(workspace)
    open("test_file_A", "wb").close()
    git_repo.add(workspace / "test_file_A")
    git_status = subprocess.run(["git", "status"], capture_output=True)
    print(git_status.stdout)
    assert git_status.returncode == 0
    assert "test_file_A" in re.search(r"new file:[ ]+([\w\W]*?)\n", git_status.stdout.decode())[1]

def test_commit():
    git_repo = GitControl(workspace)
    git_repo.commit("init test source control",
                    author = {"name": "foo", "email":"author@example.local"},
                    committer= {"name": "bar", "email":"commiter@example.local"},
                    )
    os.chdir(workspace)
    git_log = subprocess.run(["git", "log"], capture_output=True)
    print(git_log.stdout)
    assert git_log.returncode == 0
    assert b"init test source control" in git_log.stdout

def test_add_and_commit():
    git_repo = GitControl(workspace)
    os.chdir(workspace)
    open("README.md", "wb").close()
    open("requirements.txt", "wb").close()
    if(not os.path.exists("child_dir")):
        os.mkdir("child_dir")
    open("child_dir/LICENSE", "wb").close()
    file_list = [workspace / "README.md", workspace / "requirements.txt",
                 workspace /"child_dir" / "LICENSE"]
    git_repo.add_and_commit(workspace,
                            file_list,
                            author = {"name": "foo", "email":"author@example.local"},
                            # committer= {"name": "bar", "email":"commiter@example.local"},
                            )
    git_log = subprocess.run(["git", "log"], capture_output=True)
    print(git_log.stdout)
    assert git_log.returncode == 0
    assert b"add files: /README.md /requirements.txt /child_dir/LICENSE" in git_log.stdout

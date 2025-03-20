#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:09
@Author  : alexanderwu
@File    : workspace_config.py
"""
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import field_validator, model_validator

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.utils.yaml_model import YamlModel


class WorkspaceConfig(YamlModel):
    path: Path = DEFAULT_WORKSPACE_ROOT
    use_uid: bool = False
    uid: str = ""

    @field_validator("path")
    @classmethod
    def check_workspace_path(cls, v):
        if isinstance(v, str):
            v = Path(v)
        return v

    @model_validator(mode="after")
    def check_uid_and_update_path(self):
        if self.use_uid and not self.uid:
            self.uid = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[-8:]}"
            self.path = self.path / self.uid

        # Create workspace path if not exists
        self.path.mkdir(parents=True, exist_ok=True)
        return self

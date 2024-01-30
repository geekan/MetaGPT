#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:09
# @Author  : alexanderwu
# @File    : workspace_config.py

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import field_validator, model_validator

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.utils.yaml_model import YamlModel


class WorkspaceConfig(YamlModel):
    """Configuration for the workspace.

    Attributes:
        path: The file system path to the workspace.
        use_uid: Flag to determine if a unique identifier should be used in the path.
        uid: The unique identifier to be appended to the path if use_uid is True.

    """

    path: Path = DEFAULT_WORKSPACE_ROOT
    use_uid: bool = False
    uid: str = ""

    @field_validator("path")
    @classmethod
    def check_workspace_path(cls, v):
        """Validates and possibly transforms the workspace path.

        Args:
            v: The value of the path field, either a Path object or a string that can be converted to a Path.

        Returns:
            The validated and possibly transformed path as a Path object.
        """
        if isinstance(v, str):
            v = Path(v)
        return v

    @model_validator(mode="after")
    def check_uid_and_update_path(self):
        """Checks if UID is needed and not present, generates it, and updates the path accordingly.

        This method is called after model validation. If use_uid is True and uid is not set, it generates a new uid
        and updates the path to include the uid. It also ensures the path exists.

        Returns:
            The instance of WorkspaceConfig with possibly updated uid and path.
        """
        if self.use_uid and not self.uid:
            self.uid = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[-8:]}"
            self.path = self.path / self.uid

        # Create workspace path if not exists
        self.path.mkdir(parents=True, exist_ok=True)
        return self

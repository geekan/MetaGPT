#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field


class BaseEnvActionType(IntEnum):
    # # NONE = 0  # no action to run, just get observation
    pass


class BaseEnvAction(BaseModel):
    """env action type and its related params of action functions/apis"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    action_type: int = Field(default=0, description="action type")


class BaseEnvObsType(IntEnum):
    # # NONE = 0                     # get whole observation from env
    pass


class BaseEnvObsParams(BaseModel):
    """observation params for different EnvObsType to get its observe result"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    obs_type: int = Field(default=0, description="observation type")

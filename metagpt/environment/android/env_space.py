#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from pathlib import Path
from typing import Union

import numpy as np
import numpy.typing as npt
from gymnasium import spaces
from pydantic import ConfigDict, Field, field_validator

from metagpt.environment.base_env_space import (
    BaseEnvAction,
    BaseEnvActionType,
    BaseEnvObsParams,
    BaseEnvObsType,
)


class EnvActionType(BaseEnvActionType):
    NONE = 0  # no action to run, just get observation

    SYSTEM_BACK = 1
    SYSTEM_TAP = 2
    USER_INPUT = 3
    USER_LONGPRESS = 4
    USER_SWIPE = 5
    USER_SWIPE_TO = 6


class EnvAction(BaseEnvAction):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    action_type: int = Field(default=EnvActionType.NONE, description="action type")
    coord: npt.NDArray[np.int64] = Field(
        default_factory=lambda: np.zeros(2, dtype=np.int64), description="operation coordinate"
    )
    tgt_coord: npt.NDArray[np.int64] = Field(
        default_factory=lambda: np.zeros(2, dtype=np.int64), description="target operation coordinate"
    )
    input_txt: str = Field(default="", description="user input text")
    orient: str = Field(default="up", description="swipe orient")
    dist: str = Field(default="medium", description="swipe dist")

    @field_validator("coord", "tgt_coord", mode="before")
    @classmethod
    def check_coord(cls, coord) -> npt.NDArray[np.int64]:
        if not isinstance(coord, np.ndarray):
            return np.array(coord)


class EnvObsType(BaseEnvObsType):
    NONE = 0  # get whole observation from env

    GET_SCREENSHOT = 1
    GET_XML = 2


class EnvObsParams(BaseEnvObsParams):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    obs_type: int = Field(default=EnvObsType.NONE, description="observation type")
    ss_name: str = Field(default="", description="screenshot file name")
    xml_name: str = Field(default="", description="xml file name")
    local_save_dir: Union[str, Path] = Field(default="", description="local dir to save file")


EnvObsValType = str


def get_observation_space() -> spaces.Dict:
    space = spaces.Dict({"screenshot": spaces.Text(256), "xml": spaces.Text(256)})
    return space


def get_action_space(device_shape: tuple[int, int]) -> spaces.Dict:
    space = spaces.Dict(
        {
            "action_type": spaces.Discrete(len(EnvActionType)),
            "coord": spaces.Box(
                np.array([0, 0], dtype=np.int64), np.array([device_shape[0], device_shape[1]], dtype=np.int64)
            ),
            "tgt_coord": spaces.Box(
                np.array([0, 0], dtype=np.int64), np.array([device_shape[0], device_shape[1]], dtype=np.int64)
            ),
            "input_txt": spaces.Text(256),
            "orient": spaces.Text(16),
            "dist": spaces.Text(16),
        }
    )
    return space

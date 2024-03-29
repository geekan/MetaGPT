#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from typing import Any, Optional, Union

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

    ADD_TILE_EVENT = 1  # Add an event triple to a tile
    RM_TILE_EVENT = 2  # Remove an event triple from a tile
    TURN_TILE_EVENT_IDLE = 3  # Turn an event triple from a tile into idle
    RM_TITLE_SUB_EVENT = 4  # Remove an event triple that has the input subject from a tile


class EnvAction(BaseEnvAction):
    """env action type and its related params of action functions/apis"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    action_type: int = Field(default=EnvActionType.NONE, description="action type")
    coord: npt.NDArray[np.int64] = Field(
        default_factory=lambda: np.zeros(2, dtype=np.int64), description="tile coordinate"
    )
    subject: str = Field(default="", description="subject name of first element in event")
    event: tuple[str, Optional[str], Optional[str], Optional[str]] = Field(
        default=["", None, None, None], description="tile event"
    )

    @field_validator("coord", mode="before")
    @classmethod
    def check_coord(cls, coord) -> npt.NDArray[np.int64]:
        if not isinstance(coord, np.ndarray):
            return np.array(coord)


class EnvObsType(BaseEnvObsType):
    """get part observation with specific params"""

    NONE = 0  # get whole observation from env

    GET_TITLE = 1  # get the tile detail dictionary with given tile coord
    TILE_PATH = 2  # get the tile address with given tile coord
    TILE_NBR = 3  # get the neighbors of given tile coord and its vision radius


class EnvObsParams(BaseEnvObsParams):
    """observation params for different EnvObsType"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    obs_type: int = Field(default=EnvObsType.NONE, description="observation type")
    coord: npt.NDArray[np.int64] = Field(
        default_factory=lambda: np.zeros(2, dtype=np.int64), description="tile coordinate"
    )
    level: str = Field(default="", description="different level of title")
    vision_radius: int = Field(default=0, description="the vision radius of current tile")

    @field_validator("coord", mode="before")
    @classmethod
    def check_coord(cls, coord) -> npt.NDArray[np.int64]:
        if not isinstance(coord, np.ndarray):
            return np.array(coord)


EnvObsValType = Union[list[list[str]], dict[str, set[tuple[int, int]]], list[list[dict[str, Any]]]]


def get_observation_space() -> spaces.Dict:
    # it's a
    space = spaces.Dict(
        {"collision_maze": spaces.Discrete(2), "tiles": spaces.Discrete(2), "address_tiles": spaces.Discrete(2)}
    )

    return space


def get_action_space(maze_shape: tuple[int, int]) -> spaces.Dict:
    """The fields defined by the space correspond to the input parameters of the action except `action_type`"""
    space = spaces.Dict(
        {
            "action_type": spaces.Discrete(len(EnvActionType)),
            "coord": spaces.Box(
                np.array([0, 0], dtype=np.int64), np.array([maze_shape[0], maze_shape[1]], dtype=np.int64)
            ),  # coord of the tile
            "subject": spaces.Text(256),  # the first element of an tile event
            "event": spaces.Tuple(
                (spaces.Text(256), spaces.Text(256), spaces.Text(256), spaces.Text(256))
            ),  # event is a tuple of four str
        }
    )
    return space

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import typing
from typing import Any
import json
from pathlib import Path
import importlib
from tenacity import _utils
import traceback
from pydantic.json import pydantic_encoder

from metagpt.logs import logger


def general_after_log(logger: "loguru.Logger", sec_format: str = "%0.3f") -> typing.Callable[["RetryCallState"], None]:
    def log_it(retry_state: "RetryCallState") -> None:
        if retry_state.fn is None:
            fn_name = "<unknown>"
        else:
            fn_name = _utils.get_callback_name(retry_state.fn)
        logger.error(
            f"Finished call to '{fn_name}' after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it. "
            f"exp: {retry_state.outcome.exception()}"
        )

    return log_it


def read_json_file(json_file: str, encoding=None) -> list[Any]:
    if not Path(json_file).exists():
        raise FileNotFoundError(f"json_file: {json_file} not exist, return []")

    with open(json_file, "r", encoding=encoding) as fin:
        try:
            data = json.load(fin)
        except Exception as exp:
            raise ValueError(f"read json file: {json_file} failed")
    return data


def write_json_file(json_file: str, data: list, encoding=None):
    folder_path = Path(json_file).parent
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    with open(json_file, "w", encoding=encoding) as fout:
        json.dump(data, fout, ensure_ascii=False, indent=4, default=pydantic_encoder)


def import_class(class_name: str, module_name: str) -> type:
    module = importlib.import_module(module_name)
    a_class = getattr(module, class_name)
    return a_class


def import_class_inst(class_name: str, module_name: str, *args, **kwargs) -> object:
    a_class = import_class(class_name, module_name)
    class_inst = a_class(*args, **kwargs)
    return class_inst


def format_trackback_info(limit: int = 2):
    return traceback.format_exc(limit=limit)


def serialize_decorator(func):
    async def wrapper(self, *args, **kwargs):
        try:
            result = await func(self, *args, **kwargs)
            self.serialize()  # Team.serialize
            return result
        except KeyboardInterrupt as kbi:
            logger.error(f"KeyboardInterrupt occurs, start to serialize the project, exp:\n{format_trackback_info()}")
            self.serialize()  # Team.serialize
        except Exception as exp:
            logger.error(f"Exception occurs, start to serialize the project, exp:\n{format_trackback_info()}")
            self.serialize()  # Team.serialize

    return wrapper


def role_raise_decorator(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except KeyboardInterrupt as kbi:
            logger.error(f"KeyboardInterrupt: {kbi} occurs, start to serialize the project")
            if self._rc.env:
                newest_msgs = self._rc.env.memory.get(1)
                if len(newest_msgs) > 0:
                    self._rc.memory.delete(newest_msgs[0])
            raise Exception(format_trackback_info(limit=None))  # raise again to make it captured outside
        except Exception as exp:
            if self._rc.env:
                newest_msgs = self._rc.env.memory.get(1)
                if len(newest_msgs) > 0:
                    logger.warning("There is a exception in role's execution, in order to resume, "
                                   "we delete the newest role communication message in the role's memory.")
                    self._rc.memory.delete(newest_msgs[0])  # remove newest msg of the role to make it observed again
            raise Exception(format_trackback_info(limit=None))  # raise again to make it captured outside

    return wrapper

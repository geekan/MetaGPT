#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/4/25
@Author  : mashenquan
@File    : env.py
@Desc: Implement `get_env`. RFC 216 2.4.2.4.2.
"""
import os

from metagpt.context import Context


class EnvKeyNotFoundError(Exception):
    def __init__(self, info):
        super().__init__(info)


async def default_get_env(key: str, app_name: str = None) -> str:
    if key in os.environ:
        return os.environ[key]
    context = Context()
    val = context.kwargs.get(key, None)
    if val is not None:
        return val

    raise EnvKeyNotFoundError(f"EnvKeyNotFoundError: {key}, app_name:{app_name or ''}")


_get_env_entry = default_get_env


async def get_env(key: str, app_name: str = None) -> str:
    """
    Retrieve the value of the environment variable for the specified key.

    Args:
        key (str): The key of the environment variable.
        app_name (str, optional): The name of the application. Defaults to None.

    Returns:
        str: The value corresponding to the given key in the environment variables.
             If no value is found for the given key, an empty string is returned.

    Example:
        This function can be used to retrieve environment variables asynchronously.
        It should be called using `await`.

        >>> from metagpt.tools.libs.env import get_env
        >>> api_key = await get_env("API_KEY")
        >>> print(api_key)
        <API_KEY>

        >>> from metagpt.tools.libs.env import get_env
        >>> api_key = await get_env(key="API_KEY", app_name="GITHUB")
        >>> print(api_key)
        <API_KEY>

    Note:
        This is an asynchronous function and must be called using `await`.
    """
    global _get_env_entry
    if _get_env_entry:
        return await _get_env_entry(key=key, app_name=app_name)

    return await default_get_env(key=key, app_name=app_name)


def set_get_env_entry(func):
    """Modify `get_env` entry.

    Args:
        func: New function entry.
    """
    global _get_env_entry
    _get_env_entry = func

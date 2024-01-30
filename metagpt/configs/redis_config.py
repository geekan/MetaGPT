#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:06
# @Author  : alexanderwu
# @File    : redis_config.py

from metagpt.utils.yaml_model import YamlModelWithoutDefault


class RedisConfig(YamlModelWithoutDefault):
    """Configuration class for Redis connection details.

    Inherits from YamlModelWithoutDefault to parse and validate Redis configuration from YAML files.

    Attributes:
        host: The hostname of the Redis server.
        port: The port on which the Redis server is running.
        username: The username for Redis authentication (optional).
        password: The password for Redis authentication.
        db: The database number to connect to.
    """

    host: str
    port: int
    username: str = ""
    password: str
    db: str

    def to_url(self):
        """Constructs a Redis URL from the configuration.

        Returns:
            A string representing the Redis connection URL.
        """
        return f"redis://{self.host}:{self.port}"

    def to_kwargs(self):
        """Constructs a dictionary of Redis connection parameters.

        Returns:
            A dictionary with connection parameters suitable for Redis client initialization.
        """
        return {
            "username": self.username,
            "password": self.password,
            "db": self.db,
        }

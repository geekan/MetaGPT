#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 16:15
# @Author  : alexanderwu
# @File    : singleton.py

import abc


class Singleton(abc.ABCMeta, type):
    """Singleton metaclass for ensuring only one instance of a class.

    This metaclass can be used to create singleton classes, ensuring that only
    one instance of the class exists throughout the application.

    Attributes:
        _instances: A dictionary holding the instances of the singleton classes.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call method for the singleton metaclass."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

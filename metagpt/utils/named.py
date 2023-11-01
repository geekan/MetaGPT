#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/1
@Author  : mashenquan
@File    : named.py
"""


class Named:
    """A base class with functions for converting classes to names and objects to class names."""

    @classmethod
    def get_class_name(cls):
        """Return class name"""
        return f"{cls.__module__}.{cls.__name__}"

    def get_object_name(self):
        """Return class name of the object"""
        cls = type(self)
        return f"{cls.__module__}.{cls.__name__}"

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/28 14:54
@Author  : alexanderwu
@File    : inspect_module.py
"""

import inspect

import metagpt  # replace with your module


def print_classes_and_functions(module):
    """FIXME: NOT WORK.. """
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            print(f'Class: {name}')
        elif inspect.isfunction(obj):
            print(f'Function: {name}')
        else:
            print(name)

    print(dir(module))


if __name__ == '__main__':
    print_classes_and_functions(metagpt)
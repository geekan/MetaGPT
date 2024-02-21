#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : registry to store Dynamic Model from ActionNode.create_model_class to keep it as same Class
#           with same class name and mapping

from functools import wraps

action_outcls_registry = dict()


def register_action_outcls(func):
    """Decorator to register output classes for actions.

    This decorator is used to handle the dynamic creation of classes by `create_model` function. It ensures that
    classes with the same name and field definitions are identified uniquely using an `outcls_id`.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function which ensures unique identification of dynamically created classes.
    """

    @wraps(func)
    def decorater(*args, **kwargs):
        """
        arr example
            [<class 'metagpt.actions.action_node.ActionNode'>, 'test', {'field': (str, Ellipsis)}]
        """
        arr = list(args) + list(kwargs.values())
        """
        outcls_id example
            "<class 'metagpt.actions.action_node.ActionNode'>_test_{'field': (str, Ellipsis)}"
        """
        for idx, item in enumerate(arr):
            if isinstance(item, dict):
                arr[idx] = dict(sorted(item.items()))
        outcls_id = "_".join([str(i) for i in arr])
        # eliminate typing influence
        outcls_id = outcls_id.replace("typing.List", "list").replace("typing.Dict", "dict")

        if outcls_id in action_outcls_registry:
            return action_outcls_registry[outcls_id]

        out_cls = func(*args, **kwargs)
        action_outcls_registry[outcls_id] = out_cls
        return out_cls

    return decorater

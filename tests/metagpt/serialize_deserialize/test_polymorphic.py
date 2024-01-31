#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of polymorphic conditions
import copy

from pydantic import BaseModel, ConfigDict, SerializeAsAny

from metagpt.actions import Action
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    ActionOKV2,
    ActionPass,
)


class ActionSubClasses(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    actions: list[SerializeAsAny[Action]] = []


class ActionSubClassesNoSAA(BaseModel):
    """without SerializeAsAny"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    actions: list[Action] = []


def test_serialize_as_any():
    """test subclasses of action with different fields in ser&deser"""
    # ActionOKV2 with a extra field `extra_field`
    action_subcls = ActionSubClasses(actions=[ActionOKV2(), ActionPass()])
    action_subcls_dict = action_subcls.model_dump()
    assert action_subcls_dict["actions"][0]["extra_field"] == ActionOKV2().extra_field


def test_no_serialize_as_any():
    # ActionOKV2 with a extra field `extra_field`
    action_subcls = ActionSubClassesNoSAA(actions=[ActionOKV2(), ActionPass()])
    action_subcls_dict = action_subcls.model_dump()
    # without `SerializeAsAny`, it will serialize as Action
    assert "extra_field" not in action_subcls_dict["actions"][0]


def test_polymorphic():
    ok_v2 = ActionOKV2(
        **{"name": "ActionOKV2", "context": "", "prefix": "", "desc": "", "extra_field": "ActionOKV2 Extra Info"}
    )

    action_subcls = ActionSubClasses(actions=[ActionOKV2(), ActionPass()])
    action_subcls_dict = action_subcls.model_dump()
    action_subcls_dict2 = copy.deepcopy(action_subcls_dict)

    assert "__module_class_name" in action_subcls_dict["actions"][0]

    new_action_subcls = ActionSubClasses(**action_subcls_dict)
    assert isinstance(new_action_subcls.actions[0], ActionOKV2)
    assert new_action_subcls.actions[0].extra_field == ok_v2.extra_field
    assert isinstance(new_action_subcls.actions[1], ActionPass)

    new_action_subcls = ActionSubClasses.model_validate(action_subcls_dict2)
    assert isinstance(new_action_subcls.actions[0], ActionOKV2)
    assert isinstance(new_action_subcls.actions[1], ActionPass)

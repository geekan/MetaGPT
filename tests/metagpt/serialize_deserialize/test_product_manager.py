# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:07 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.roles.product_manager import ProductManager
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_product_manager_deserialize():
    role = ProductManager()
    ser_role_dict = role.dict(by_alias=True)
    new_role = ProductManager(**ser_role_dict)

    assert new_role.name == "Alice"
    assert len(new_role._actions) == 2
    assert isinstance(new_role._actions[0], Action)
    await new_role._actions[0].run([Message(content="write a cli snake game")])

# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:07 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.roles.product_manager import ProductManager
from metagpt.schema import Message


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_product_manager_deserialize():
    role = ProductManager()
    ser_role_dict = role.model_dump(by_alias=True)
    new_role = ProductManager(**ser_role_dict)

    assert new_role.name == "Alice"
    assert len(new_role.actions) == 2
    assert isinstance(new_role.actions[0], Action)
    await new_role.actions[0].run([Message(content="write a cli snake game")])

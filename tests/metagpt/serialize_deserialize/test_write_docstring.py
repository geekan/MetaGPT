# -*- coding: utf-8 -*-
# @Desc    :
import pytest

from metagpt.actions.write_docstring import WriteDocstring

code = """
def add_numbers(a: int, b: int):
    return a + b


class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old."
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("style", "part"),
    [
        ("google", "Args:"),
        ("numpy", "Parameters"),
        ("sphinx", ":param name:"),
    ],
    ids=["google", "numpy", "sphinx"],
)
@pytest.mark.usefixtures("llm_mock")
async def test_action_deserialize(style: str, part: str):
    action = WriteDocstring()
    serialized_data = action.model_dump()

    assert "name" in serialized_data
    assert serialized_data["desc"] == "Write docstring for code."

    new_action = WriteDocstring(**serialized_data)

    assert new_action.name == "WriteDocstring"
    assert new_action.desc == "Write docstring for code."
    ret = await new_action.run(code, style=style)
    assert part in ret

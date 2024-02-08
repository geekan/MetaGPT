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
async def test_write_docstring(style: str, part: str, context):
    ret = await WriteDocstring(context=context).run(code, style=style)
    assert part in ret


@pytest.mark.asyncio
async def test_write():
    code = await WriteDocstring.write_docstring(__file__)
    assert code


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

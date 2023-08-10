import pytest

from metagpt.actions.write_docstring import WriteDocstring

code = '''
def add_numbers(a: int, b: int):
    return a + b


class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old."
'''


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("style", "part"),
    [
        ("google", "Args:"),
        ("numpy", "Parameters"),
        ("sphinx", ":param name:"),
    ],
    ids=["google", "numpy", "sphinx"]
)
async def test_write_docstring(style: str, part: str):
    ret = await WriteDocstring().run(code, style=style)
    assert part in ret

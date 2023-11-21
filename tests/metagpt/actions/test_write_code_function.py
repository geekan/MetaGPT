import pytest

from metagpt.actions.write_code_function import WriteCodeFunction


@pytest.mark.asyncio
async def test_write_code():
    coder = WriteCodeFunction()
    code = await coder.run("Write a hello world code.")
    assert "language" in code.content
    assert "code" in code.content
    print(code)


@pytest.mark.asyncio
async def test_write_code_by_list_prompt():
    coder = WriteCodeFunction()
    msg = ["a=[1,2,5,10,-10]", "写出求a中最大值的代码python"]
    code = await coder.run(msg)
    assert "language" in code.content
    assert "code" in code.content
    print(code)

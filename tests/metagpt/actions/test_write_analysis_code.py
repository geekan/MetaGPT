import pytest

from metagpt.actions.write_analysis_code import WriteCodeByGenerate
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.schema import Message


# @pytest.mark.asyncio
# async def test_write_code():
#     write_code = WriteCodeFunction()
#     code = await write_code.run("Write a hello world code.")
#     assert len(code) > 0
#     print(code)


# @pytest.mark.asyncio
# async def test_write_code_by_list_prompt():
#     write_code = WriteCodeFunction()
#     msg = ["a=[1,2,5,10,-10]", "写出求a中最大值的代码python"]
#     code = await write_code.run(msg)
#     assert len(code) > 0
#     print(code)


@pytest.mark.asyncio
async def test_write_code_by_list_plan():
    write_code = WriteCodeByGenerate()
    execute_code = ExecutePyCode()
    messages = []
    plan = ["随机生成一个pandas DataFrame时间序列", "绘制这个时间序列的直方图", "求均值"]
    for task in plan:
        print(f"\n任务: {task}\n\n")
        messages.append(Message(task, role='assistant'))
        code = await write_code.run(messages)
        messages.append(Message(code, role='assistant'))
        assert len(code) > 0
        output = await execute_code.run(code)
        print(f"\n[Output]: 任务{task}的执行结果是: \n{output}\n")
        messages.append(output[0])

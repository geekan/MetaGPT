import pytest

from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.schema import Message, Plan, Task


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


@pytest.mark.asyncio
async def test_tool_recommendation():
    task = "对已经读取的数据集进行数据清洗"
    code_steps = """
    step 1: 对数据集进行去重
    step 2: 对数据集进行缺失值处理
    """
    available_tools = [
        {
            "name": "fill_missing_value",
            "description": "Completing missing values with simple strategies",
        },
        {
            "name": "split_bins",
            "description": "Bin continuous data into intervals and return the bin identifier encoded as an integer value",
        },
    ]
    write_code = WriteCodeWithTools()
    tools = await write_code._tool_recommendation(task, code_steps, available_tools)

    assert len(tools) == 2
    assert tools[0] == []
    assert tools[1] == ["fill_missing_value"]


@pytest.mark.asyncio
async def test_write_code_with_tools():
    write_code = WriteCodeWithTools()
    messages = []
    task_map = {
        "1": Task(
                task_id="1",
                instruction="随机生成一个pandas DataFrame数据集",
                task_type="unknown",
                dependent_task_ids=[],
                code="""
                import pandas as pd
                df = pd.DataFrame({
                    'a': [1, 2, 3, 4, 5],
                    'b': [1.1, 2.2, 3.3, 4.4, np.nan],
                    'c': ['aa', 'bb', 'cc', 'dd', 'ee'],
                    'd': [1, 2, 3, 4, 5]
                })
                """,
                is_finished=True,
            ),
        "2": Task(
                task_id="2",
                instruction="对数据集进行数据清洗",
                task_type="data_preprocess",
                dependent_task_ids=["1"],
            ),
    }
    plan = Plan(
        goal="构造数据集并进行数据清洗",
        tasks=list(task_map.values()),
        task_map=task_map,
        current_task_id="2",
    )
    task_guide = """
    step 1: 对数据集进行去重
    step 2: 对数据集进行缺失值处理
    """
    data_desc = "None"

    code = await write_code.run(messages, plan, task_guide, data_desc)
    assert len(code) > 0
    print(code)

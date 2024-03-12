import asyncio

import pytest

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import (
    WriteCodeWithoutTools,
    WriteCodeWithTools,
)
from metagpt.logs import logger
from metagpt.schema import Message, Plan, Task
from metagpt.strategy.planner import STRUCTURAL_CONTEXT


@pytest.mark.skip
@pytest.mark.asyncio
async def test_write_code_by_list_plan():
    write_code = WriteCodeWithoutTools()
    execute_code = ExecuteNbCode()
    messages = []
    plan = ["随机生成一个pandas DataFrame时间序列", "绘制这个时间序列的直方图", "回顾已完成的任务", "求均值", "总结"]
    for task in plan:
        print(f"\n任务: {task}\n\n")
        messages.append(Message(task, role="assistant"))
        code = await write_code.run(messages)
        if task.startswith(("回顾", "总结")):
            assert code["language"] == "markdown"
        else:
            assert code["language"] == "python"
        messages.append(Message(code["code"], role="assistant"))
        assert len(code) > 0
        output, _ = await execute_code.run(**code)
        print(f"\n[Output]: 任务{task}的执行结果是: \n{output}\n")
        messages.append(output)


@pytest.mark.asyncio
async def test_tool_recommendation():
    task = "clean and preprocess the data"
    available_tools = {
        "FillMissingValue": "Filling missing values",
        "SplitBins": "Bin continuous data into intervals and return the bin identifier encoded as an integer value",
    }
    write_code = WriteCodeWithTools()
    tools = await write_code._recommend_tool(task, available_tools)

    assert len(tools) == 1
    assert "FillMissingValue" in tools


@pytest.mark.asyncio
async def test_write_code_with_tools():
    write_code = WriteCodeWithTools()

    requirement = "构造数据集并进行数据清洗"
    task_map = {
        "1": Task(
            task_id="1",
            instruction="随机生成一个pandas DataFrame数据集",
            task_type="other",
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

    context = STRUCTURAL_CONTEXT.format(
        user_requirement=requirement,
        context=plan.context,
        tasks=list(task_map.values()),
        current_task=plan.current_task.model_dump_json(),
    )
    context_msg = [Message(content=context, role="user")]

    code = await write_code.run(context_msg, plan)
    code = code["code"]
    assert len(code) > 0
    print(code)


@pytest.mark.asyncio
async def test_write_code_to_correct_error():
    structural_context = """
    ## User Requirement
    read a dataset test.csv and print its head
    ## Current Plan
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "import pandas and load the dataset from 'test.csv'.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        },
        {
            "task_id": "2",
            "dependent_task_ids": [
                "1"
            ],
            "instruction": "Print the head of the dataset to display the first few rows.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        }
    ]
    ## Current Task
    {"task_id": "1", "dependent_task_ids": [], "instruction": "import pandas and load the dataset from 'test.csv'.", "task_type": "", "code": "", "result": "", "is_finished": false}
    """
    wrong_code = """import pandas as pd\ndata = pd.read_excel('test.csv')\ndata"""  # use read_excel to read a csv
    error = """
    Traceback (most recent call last):
        File "<stdin>", line 2, in <module>
        File "/Users/gary/miniconda3/envs/py39_scratch/lib/python3.9/site-packages/pandas/io/excel/_base.py", line 478, in read_excel
            io = ExcelFile(io, storage_options=storage_options, engine=engine)
        File "/Users/gary/miniconda3/envs/py39_scratch/lib/python3.9/site-packages/pandas/io/excel/_base.py", line 1500, in __init__
            raise ValueError(
        ValueError: Excel file format cannot be determined, you must specify an engine manually.
    """
    context = [
        Message(content=structural_context, role="user"),
        Message(content=wrong_code, role="assistant"),
        Message(content=error, role="user"),
    ]
    new_code = await WriteCodeWithoutTools().run(context=context)
    new_code = new_code["code"]
    print(new_code)
    assert "read_csv" in new_code  # should correct read_excel to read_csv


@pytest.mark.asyncio
async def test_write_code_reuse_code_simple():
    structural_context = """
    ## User Requirement
    read a dataset test.csv and print its head
    ## Current Plan
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "import pandas and load the dataset from 'test.csv'.",
            "task_type": "",
            "code": "import pandas as pd\ndata = pd.read_csv('test.csv')",
            "result": "",
            "is_finished": true
        },
        {
            "task_id": "2",
            "dependent_task_ids": [
                "1"
            ],
            "instruction": "Print the head of the dataset to display the first few rows.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        }
    ]
    ## Current Task
    {"task_id": "2", "dependent_task_ids": ["1"], "instruction": "Print the head of the dataset to display the first few rows.", "task_type": "", "code": "", "result": "", "is_finished": false}
    """
    context = [
        Message(content=structural_context, role="user"),
    ]
    code = await WriteCodeWithoutTools().run(context=context)
    code = code["code"]
    print(code)
    assert "pandas" not in code and "read_csv" not in code  # should reuse import and read statement from previous one


@pytest.mark.skip
@pytest.mark.asyncio
async def test_write_code_reuse_code_long():
    """test code reuse for long context"""

    structural_context = """
    ## User Requirement
    Run data analysis on sklearn Iris dataset, include a plot
    ## Current Plan
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Load the Iris dataset from sklearn.",
            "task_type": "",
            "code": "from sklearn.datasets import load_iris\niris_data = load_iris()\niris_data['data'][0:5], iris_data['target'][0:5]",
            "result": "(array([[5.1, 3.5, 1.4, 0.2],\n        [4.9, 3. , 1.4, 0.2],\n        [4.7, 3.2, 1.3, 0.2],\n        [4.6, 3.1, 1.5, 0.2],\n        [5. , 3.6, 1.4, 0.2]]),\n array([0, 0, 0, 0, 0]))",
            "is_finished": true
        },
        {
            "task_id": "2",
            "dependent_task_ids": [
                "1"
            ],
            "instruction": "Perform exploratory data analysis on the Iris dataset.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        },
        {
            "task_id": "3",
            "dependent_task_ids": [
                "2"
            ],
            "instruction": "Create a plot visualizing the Iris dataset features.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        }
    ]
    ## Current Task
    {"task_id": "2", "dependent_task_ids": ["1"], "instruction": "Perform exploratory data analysis on the Iris dataset.", "task_type": "", "code": "", "result": "", "is_finished": false}
    """
    context = [
        Message(content=structural_context, role="user"),
    ]
    trials_num = 5
    trials = [WriteCodeWithoutTools().run(context=context, temperature=0.0) for _ in range(trials_num)]
    trial_results = await asyncio.gather(*trials)
    print(*trial_results, sep="\n\n***\n\n")
    success = [
        "load_iris" not in result["code"] and "iris_data" in result["code"] for result in trial_results
    ]  # should reuse iris_data from previous tasks
    success_rate = sum(success) / trials_num
    logger.info(f"success rate: {success_rate :.2f}")
    assert success_rate >= 0.8


@pytest.mark.skip
@pytest.mark.asyncio
async def test_write_code_reuse_code_long_for_wine():
    """test code reuse for long context"""

    structural_context = """
    ## User Requirement
    Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy
    ## Current Plan
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Load the sklearn Wine recognition dataset and perform exploratory data analysis."
            "task_type": "",
            "code": "from sklearn.datasets import load_wine\n# Load the Wine recognition dataset\nwine_data = load_wine()\n# Perform exploratory data analysis\nwine_data.keys()",
            "result": "Truncated to show only the last 1000 characters\ndict_keys(['data', 'target', 'frame', 'target_names', 'DESCR', 'feature_names'])",
            "is_finished": true
        },
        {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Create a plot to visualize some aspect of the wine dataset."
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        },
        {
            "task_id": "3",
            "dependent_task_ids": ["1"],
            "instruction": "Split the dataset into training and validation sets with a 20% validation size.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        },
        {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Train a model on the training set to predict wine class.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        },
        {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Evaluate the model on the validation set and report the accuracy.",
            "task_type": "",
            "code": "",
            "result": "",
            "is_finished": false
        }
    ]
    ## Current Task
    {"task_id": "2", "dependent_task_ids": ["1"], "instruction": "Create a plot to visualize some aspect of the Wine dataset.", "task_type": "", "code": "", "result": "", "is_finished": false}
    """
    context = [
        Message(content=structural_context, role="user"),
    ]
    trials_num = 5
    trials = [WriteCodeWithoutTools().run(context=context, temperature=0.0) for _ in range(trials_num)]
    trial_results = await asyncio.gather(*trials)
    print(*trial_results, sep="\n\n***\n\n")
    success = [
        "load_wine" not in result["code"] and "wine_data" in result["code"] for result in trial_results
    ]  # should reuse iris_data from previous tasks
    success_rate = sum(success) / trials_num
    logger.info(f"success rate: {success_rate :.2f}")
    assert success_rate >= 0.8

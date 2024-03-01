import pytest

from metagpt.actions.di.ml_action import WriteCodeWithToolsML
from metagpt.schema import Plan, Task


@pytest.mark.asyncio
async def test_write_code_with_tools():
    write_code_ml = WriteCodeWithToolsML()

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
    column_info = ""

    _, code_with_ml = await write_code_ml.run([], plan, column_info)
    code_with_ml = code_with_ml["code"]
    assert len(code_with_ml) > 0
    print(code_with_ml)

import pytest

from metagpt.actions.ci.execute_nb_code import ExecuteNbCode
from metagpt.logs import logger
from metagpt.roles.ci.ml_engineer import MLEngineer
from metagpt.schema import Message, Plan, Task
from metagpt.tools.tool_type import ToolType
from tests.metagpt.actions.ci.test_debug_code import CODE, DebugContext, ErrorStr


def test_mle_init():
    ci = MLEngineer(goal="test", auto_run=True, use_tools=True, tools=["tool1", "tool2"])
    assert ci.tools == []


MockPlan = Plan(
    goal="This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: 'tests/data/ml_datasets/titanic/split_train.csv', eval data path: 'tests/data/ml_datasets/titanic/split_eval.csv'.",
    context="",
    tasks=[
        Task(
            task_id="1",
            dependent_task_ids=[],
            instruction="Perform exploratory data analysis on the train dataset to understand the features and target variable.",
            task_type="eda",
            code="",
            result="",
            is_success=False,
            is_finished=False,
        )
    ],
    task_map={
        "1": Task(
            task_id="1",
            dependent_task_ids=[],
            instruction="Perform exploratory data analysis on the train dataset to understand the features and target variable.",
            task_type="eda",
            code="",
            result="",
            is_success=False,
            is_finished=False,
        )
    },
    current_task_id="1",
)


@pytest.mark.asyncio
async def test_mle_write_code(mocker):
    data_path = "tests/data/ml_datasets/titanic"

    mle = MLEngineer(auto_run=True, use_tools=True)
    mle.planner.plan = MockPlan

    code, _ = await mle._write_code()
    assert data_path in code["code"]


@pytest.mark.asyncio
async def test_mle_update_data_columns(mocker):
    mle = MLEngineer(auto_run=True, use_tools=True)
    mle.planner.plan = MockPlan

    # manually update task type to test update
    mle.planner.plan.current_task.task_type = ToolType.DATA_PREPROCESS.value

    result = await mle._update_data_columns()
    assert result is not None


@pytest.mark.asyncio
async def test_mle_debug_code(mocker):
    mle = MLEngineer(auto_run=True, use_tools=True)
    mle.working_memory.add(Message(content=ErrorStr, cause_by=ExecuteNbCode))
    mle.latest_code = CODE
    mle.debug_context = DebugContext
    code, _ = await mle._write_code()
    assert len(code) > 0


@pytest.mark.skip
@pytest.mark.asyncio
async def test_ml_engineer():
    data_path = "tests/data/ml_datasets/titanic"
    requirement = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    tools = ["FillMissingValue", "CatCross", "dummy_tool"]

    mle = MLEngineer(auto_run=True, use_tools=True, tools=tools)
    rsp = await mle.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0

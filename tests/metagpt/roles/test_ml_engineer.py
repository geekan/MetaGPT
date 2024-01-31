import pytest

from metagpt.logs import logger
from metagpt.roles.ml_engineer import MLEngineer


def test_mle_init():
    ci = MLEngineer(goal="test", auto_run=True, use_tools=True, tools=["tool1", "tool2"])
    assert ci.tools == []


@pytest.mark.asyncio
async def test_ml_engineer():
    data_path = "tests/data/ml_datasets/titanic"
    requirement = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    tools = ["FillMissingValue", "CatCross", "dummy_tool"]

    mle = MLEngineer(goal=requirement, auto_run=True, use_tools=True, tools=tools)
    rsp = await mle.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0

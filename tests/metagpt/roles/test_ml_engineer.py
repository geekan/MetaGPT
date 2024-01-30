import pytest

from metagpt.const import DATA_PATH
from metagpt.logs import logger
from metagpt.roles.ml_engineer import MLEngineer


def test_mle_init():
    ci = MLEngineer(goal="test", auto_run=True, use_tools=True, tools=["tool1", "tool2"])
    assert ci.tools == []


@pytest.mark.asyncio
@pytest.mark.parametrize("use_tools", [(True)])
async def test_code_interpreter(use_tools):
    # requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    # requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    data_path = f"{DATA_PATH}/titanic"
    requirement = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    # data_path = f"{DATA_PATH}/icr-identify-age-related-conditions"
    # requirement = f"This is a medical dataset with over fifty anonymized health characteristics linked to three age-related conditions. Your goal is to predict whether a subject has or has not been diagnosed with one of these conditions.The target column is Class. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report f1 score on the eval data. Train data path: {data_path}/split_train.csv, eval data path: {data_path}/split_eval.csv."
    # data_path = f"{DATA_PATH}/santander-customer-transaction-prediction"
    # requirement = f"This is a customers financial dataset. Your goal is to predict which customers will make a specific transaction in the future. The target column is target. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report AUC Score on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv' ."
    # data_path = f"{DATA_PATH}/house-prices-advanced-regression-techniques"
    # requirement = f"This is a house price dataset, your goal is to predict the sale price of a property based on its features. The target column is SalePrice. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report RMSE between the logarithm of the predicted value and the logarithm of the observed sales price on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    tools = ["FillMissingValue", "CatCross", "dummy_tool"]

    mle = MLEngineer(goal=requirement, auto_run=True, use_tools=use_tools, tools=tools)
    rsp = await mle.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0

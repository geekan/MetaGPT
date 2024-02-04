import fire

from metagpt.actions.ci.execute_nb_code import ExecuteNbCode
from metagpt.const import DATA_PATH
from metagpt.logs import logger
from metagpt.roles.code_interpreter import CodeInterpreter
from metagpt.roles.ml_engineer import MLEngineer
from metagpt.schema import Plan
from metagpt.utils.recovery_util import load_history, save_history


async def run_code_interpreter(role_class, requirement, auto_run, use_tools, save_dir, tools):
    """
    The main function to run the MLEngineer with optional history loading.

    Args:
        requirement (str): The requirement for the MLEngineer.
        auto_run (bool): Whether to auto-run the MLEngineer.
        save_dir (str): The directory from which to load the history or to save the new history.

    Raises:
        Exception: If an error occurs during execution, log the error and save the history.
    """

    if role_class == "ci":
        role = CodeInterpreter(auto_run=auto_run, use_tools=use_tools, tools=tools)
    else:
        role = MLEngineer(
            auto_run=auto_run,
            use_tools=use_tools,
            tools=tools,
        )

    if save_dir:
        logger.info("Resuming from history trajectory")
        plan, nb = load_history(save_dir)
        role.planner.plan = Plan(**plan)
        role.execute_code = ExecuteNbCode(nb)

    else:
        logger.info("Run from scratch")

    try:
        await role.run(requirement)
    except Exception as e:
        logger.exception(f"An error occurred: {e}, save trajectory here: {save_path}")

    save_history(role, save_dir)


if __name__ == "__main__":
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

    save_dir = ""

    # role_class = "ci"
    role_class = "mle"
    auto_run = True
    use_tools = True
    tools = []
    # tools = ["FillMissingValue", "CatCross", "non_existing_test"]

    async def main(
        role_class: str = role_class,
        requirement: str = requirement,
        auto_run: bool = auto_run,
        use_tools: bool = use_tools,
        save_dir: str = save_dir,
        tools=tools,
    ):
        await run_code_interpreter(role_class, requirement, auto_run, use_tools, save_dir, tools)

    fire.Fire(main)

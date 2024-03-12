import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(requirement: str):
    role = DataInterpreter(use_reflection=True, tools=["<all>"])
    await role.run(requirement)


if __name__ == "__main__":
    data_path = "your_path_to_icr/icr-identify-age-related-conditions"
    train_path = f"{data_path}/your_train_data.csv"
    eval_path = f"{data_path}/your_eval_data.csv"
    requirement = f"This is a medical dataset with over fifty anonymized health characteristics linked to three age-related conditions. Your goal is to predict whether a subject has or has not been diagnosed with one of these conditions.The target column is Class. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report f1 score on the eval data. Train data path: {train_path}, eval data path:{eval_path}."
    asyncio.run(main(requirement))

import asyncio

from metagpt.roles.ci.ml_engineer import MLEngineer


async def main(requirement: str, auto_run: bool = True, use_tools: bool = True):
    role = MLEngineer(goal=requirement, auto_run=auto_run, use_tools=use_tools)
    await role.run(requirement)


if __name__ == "__main__":
    data_path = "your_path_to_icr/icr-identify-age-related-conditions"  # 替换 'your_path_to_icr' 为实际数据存放的路径
    train_path = f"{data_path}/your_train_data.csv"  # 替换 'your_train_data.csv' 为你的训练数据文件名
    eval_path = f"{data_path}/your_eval_data.csv"  # 替换 'your_eval_data.csv' 为你的评估数据文件名
    requirement = f"This is a medical dataset with over fifty anonymized health characteristics linked to three age-related conditions. Your goal is to predict whether a subject has or has not been diagnosed with one of these conditions.The target column is Class. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report f1 score on the eval data. Train data path: {train_path}, eval data path:{eval_path}."
    asyncio.run(main(requirement))

import os
import time

import aide

os.environ["OPENAI_API_KEY"] = "sk-xxx"
os.environ["OPENAI_BASE_URL"] = "your url"

start_time = time.time()

data_dir = "xxx/data/titanic"

goal = f"""
# User requirement
({data_dir}, 'This is a 04_titanic dataset. Your goal is to predict the target column `Survived`.\nPerform data analysis, data preprocessing, feature engineering, and modeling to predict the target. \nReport f1 on the eval data. Do not plot or make any visualizations.\n')

# Data dir
training (with labels): train.csv
testing (without labels): test.csv
dataset description: dataset_info.json (You can use this file to get additional information about the dataset)"""

exp = aide.Experiment(
    data_dir=data_dir,  # replace this with your own directory
    goal=goal,
    eval="f1",  # replace with your own evaluation metric
)

best_solution = exp.run(steps=10)

print(f"Best solution has validation metric: {best_solution.valid_metric}")
print(f"Best solution code: {best_solution.code}")
end_time = time.time()
execution_time = end_time - start_time

print(f"run time : {execution_time} seconds")

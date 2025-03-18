from metagpt.ext.opt_code.meta_agent import MetaAgent
from metagpt.ext.opt_code.opt_roles.aflow_role import AflowRole
from metagpt.ext.opt_code.memory.aflow_memory import AFlowMemory
from metagpt.ext.opt_code.search_algorithm.aflow_search import AFlowSearch
from metagpt.configs.models_config import ModelsConfig

from metagpt.ext.opt_code.memory.sela_memory import SelaMemory
from metagpt.ext.opt_code.opt_roles.sela_role import SelaRole
from metagpt.ext.opt_code.search_algorithm.sela_search import SelaSearch

import asyncio
import os

AFLOW_INIT_CODE = """
class Workflow:
    def __init__(
        self,
        name: str,
        llm_config,
        dataset: DatasetType,
    ) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        self.custom = operator.Custom(self.llm)

    async def __call__(self, problem: str):
        solution = await self.custom(input=problem, instruction=prompt_custom.PROMPT)
        return solution['response'], self.llm.cost_manager.total_cost
"""

async def aflowmain():
    memory = AFlowMemory()

    search_configs = {
        "root_path": "metagpt/ext/opt_code/data",
        "operators": ["Custom", "ScEnsemble", "AnswerGenerate"],
        "data_type": "QuestionAnswering"
    }
    search_algorithm = AFlowSearch(search_configs)

    role = AflowRole()
    meta_agent = MetaAgent(
        search_memory=memory,
        search_algorithm=search_algorithm,
        experimenter=role,
        task_name="HotpotQA"
    )

    running_configs = {
        "num_iterations": 3,
        "init_code": AFLOW_INIT_CODE,
        "init_prompt": "PROMPT = 'Please think step by step.'",
        "instruction": "",
        "llm_config": ModelsConfig.default().get("claude-3-5-sonnet-20240620"),
        "exec_llm_config": ModelsConfig.default().get("gpt-4o-mini"),
        "dataset": "HotpotQA"
    }
    await meta_agent.run(running_configs)

TASK_PROMPT = """
# User requirement
{user_requirement}
{additional_instruction}
# Data dir
train set (with labels): {train_path}
dev set (with labels): {dev_path}
test set (without labels): {test_path}
dataset description: {data_info_path} (During EDA, you can use this file to get additional information about the dataset)
"""

ADDITIONAL_INSTRUCTION = """
## Attention
1. Please do not leak the target label in any form during training.
2. Test set does not have the target column.
3. When conducting data exploration or analysis, print out the results of your findings.
4. You should perform transformations on train, dev, and test sets at the same time (it's a good idea to define functions for this and avoid code repetition).
5. When scaling or transforming features, make sure the target column is not included.
6. You could utilize dev set to validate and improve model training.

## Saving Dev and Test Predictions
1. Save the prediction results of BOTH the dev set and test set in `dev_predictions.csv` and `test_predictions.csv` respectively in the output directory. 
- Both files should contain a single column named `target` with the predicted values.
2. Make sure the prediction results are in the same format as the target column in the original training set. 
- For instance, if the original target column is a list of string, the prediction results should also be strings.

## Output Performance
Print the train and dev set performance in the last step.

# Output dir
metagpt/ext/opt_code/optimized/{task}/sela
"""

DATASET_CONFIGS = {
    "titanic": {
        "dataset": "titanic",
        "metric": "f1",
        "target_col": "Survived",
        "user_requirement": "This is a titanic dataset. Your goal is to predict the target column `Survived`.\nPerform data analysis, data preprocessing, feature engineering, and modeling to predict the target. \nReport f1 on the eval data. Do not plot or make any visualizations.\n",
    }
}

def get_split_dataset_path(task: str, data_config: dict):
    return {
        "train": os.path.join(data_config["datasets_dir"], f"split_train.csv"),
        "dev": os.path.join(data_config["datasets_dir"], f"split_dev.csv"),
        "dev_wo_target": os.path.join(data_config["datasets_dir"], f"split_dev_wo_target.csv"),
        "dev_target": os.path.join(data_config["datasets_dir"], f"split_dev_target.csv"),
        "test": os.path.join(data_config["datasets_dir"], f"split_test.csv"),
        "test_wo_target": os.path.join(data_config["datasets_dir"], f"split_test_wo_target.csv"),
        "test_target": os.path.join(data_config["datasets_dir"], f"split_test_target.csv")
    }


def create_initial_state(task: str):
    root_path = "metagpt/ext/opt_code/data/{task}"
    user_requirement = TASK_PROMPT.format(
        user_requirement = DATASET_CONFIGS[task]["user_requirement"],
        additional_instruction = ADDITIONAL_INSTRUCTION.format(task=task),
        train_path = os.path.join(root_path.format(task=task), "split_train.csv"),
        dev_path = os.path.join(root_path.format(task=task), "split_dev.csv"),
        test_path = os.path.join(root_path.format(task=task), "split_test_wo_target.csv"),
        data_info_path = os.path.join(root_path.format(task=task), "dataset_info.json"),
    )

    data_config = {
        "datasets_dir": root_path.format(task=task),
        "work_dir": f"metagpt/ext/opt_code/optimized/{task}/sela",
        "role_dir": f"metagpt/ext/opt_code/optimized/{task}/sela/roles",
        "datasets": DATASET_CONFIGS
    }

    dataset_config = DATASET_CONFIGS[task]
    datasets_dir = get_split_dataset_path(task, data_config)
    exp_pool_path = os.path.join(data_config["datasets_dir"], "ds_analysis_pool.json")

    initial_state = {
        "task": task,
        "work_dir": data_config["work_dir"],
        "node_dir": os.path.join(data_config["work_dir"], "nodes"),
        "dataset_config": dataset_config,
        "datasets_dir": datasets_dir,  # won't be used if external eval is used
        "exp_pool_path": exp_pool_path,
        "requirement": user_requirement,
        "has_run": False,
        "start_task_id": 1,
        "low_is_better": False,
        "role_timeout": 1000,
        "external_eval": True,
        "custom_dataset_dir": None
    }
    os.makedirs(initial_state["node_dir"], exist_ok=True)
    return initial_state


async def main():
    ds_config = ModelsConfig.default().get("gpt-4o-mini")
    memory = SelaMemory()
    task = "titanic"


    search_configs = {
        "max_children": 3,
        "llm_config": ds_config,
        "exp_pool_path": "metagpt/ext/opt_code/data/titanic/ds_analysis_pool.json"
    }
    search = SelaSearch(search_configs)
    role = SelaRole(
        llm_config=ds_config,
        node_id="0",
        start_task_id=1,
        role_timeout=1000,
    )

    initial_state = create_initial_state(task)
    initial_state["llm_config"] = ds_config


    running_config = {
        "state": initial_state,
        "num_iterations": 3,
        "dataset": task,
        "llm_config": ds_config,
        "instruction": ""
    }

    meta_agent = MetaAgent(
        search_memory=memory,
        search_algorithm=search,
        experimenter=role,
        task_name=task
    )
    await meta_agent.run(running_config)

if __name__ == "__main__":
    asyncio.run(aflowmain())
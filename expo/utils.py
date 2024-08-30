import yaml
from examples.MCTS_test.dataset import get_user_requirement, get_split_dataset_path
from metagpt.roles.role import Role
from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.utils.save_code import save_code_file
# from nbclient import NotebookClient
from nbformat.notebooknode import NotebookNode
import nbformat
from pathlib import Path
from loguru import logger as _logger
from datetime import datetime
import sys
import os
import re

TASK_PROMPT = """\
# User requirement
{user_requirement}
**Attention** Please do not leak the target label in any form during training.

## Saving Dev and Test Predictions
Save the prediction results of the dev set and test set in `dev_predictions.csv` and `test_predictions.csv` respectively in the output directory BEFORE printig out the results. 
The file should contain a single `target` column with the predicted values.
Make sure the prediction results are in the same format as the target column in the training set. The labels should be transformed back to the original format if any transformation was applied during training.

## Output Training Set Performance
Make sure the performance of the model is printed in python in the last step even if it has been printed in the previous steps. The value should be a float number.
Print the training set performance in the last step. Write in this format:
```python
...
print("Train score:", train_score)
```

# Data dir
training: {train_path}
dev: {dev_path}
testing: {test_path}

# Output dir
{output_dir}

"""

def load_data_config(file_path="data.yaml"):
    with open(file_path, 'r') as stream:
        data_config = yaml.safe_load(stream)
    return data_config

DATA_CONFIG = load_data_config()

def get_mcts_logger():
    print_level = "INFO"
    print_level2 = "MCTS"
    logfile_level="MCTS"
    name: str = None
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date  # name a log with prefix name

    _logger.remove()
    new_level = _logger.level(logfile_level, color="<green>", no=25)
    _logger.add(sys.stderr, level=print_level)
    _logger.add(sys.stderr, level=print_level2)
    _logger.add(Path(DATA_CONFIG["work_dir"]) / DATA_CONFIG["role_dir"] / f"{log_name}.txt", level=logfile_level)
    _logger.propagate = False
    return _logger

mcts_logger = get_mcts_logger()


def get_exp_pool_path(task_name, data_config, pool_name="analysis_pool"):
    datasets_dir = data_config['datasets_dir']
    if task_name in data_config['datasets']:
        dataset = data_config['datasets'][task_name]
        data_path = os.path.join(datasets_dir, dataset['dataset'])
    else:
        raise ValueError(f"Dataset {task_name} not found in config file. Available datasets: {data_config['datasets'].keys()}")
    exp_pool_path = os.path.join(data_path, f"{pool_name}.json")
    return exp_pool_path

def generate_task_requirement(task_name, data_config):
    user_requirement = get_user_requirement(task_name, data_config)
    split_dataset_path = get_split_dataset_path(task_name, data_config)
    train_path = split_dataset_path["train"]
    dev_path = split_dataset_path["dev_wo_target"]
    test_path = split_dataset_path["test_wo_target"]
    work_dir = data_config["work_dir"]
    output_dir = f"{work_dir}/{task_name}"
    user_requirement = TASK_PROMPT.format(user_requirement=user_requirement, 
                                          train_path=train_path, dev_path=dev_path, test_path=test_path,
                                          output_dir=output_dir)
    return user_requirement

def change_plan(role, plan):
    print(f"Change next plan to: {plan}")
    tasks = role.planner.plan.tasks
    finished = True
    for i, task in enumerate(tasks):
        if not task.code:
            finished = False
            break
    if not finished:
        tasks[i].plan = plan
    return finished
            


def is_cell_to_delete(cell: NotebookNode) -> bool:
    if "outputs" in cell:
        for output in cell["outputs"]:
            if output and "traceback" in output:
                return True
    return False


def process_cells(nb: NotebookNode) -> NotebookNode:
    new_cells = []
    i = 1
    for cell in nb["cells"]:
        if cell["cell_type"] == "code" and not is_cell_to_delete(cell):
            cell["execution_count"] = i
            new_cells.append(cell)
            i = i + 1
    nb["cells"] = new_cells
    return nb

def save_notebook(role: Role, save_dir: str = "", name: str = ""):
    save_dir = Path(save_dir)
    nb = process_cells(role.execute_code.nb)
    save_code_file(name=name, code_context=nb, file_format="ipynb", save_dir=save_dir)

async def load_execute_notebook(role):
    tasks = role.planner.plan.tasks
    codes = [task.code for task in tasks if task.code]
    executor = role.execute_code
    # await executor.build()
    for code in codes:
        outputs, success = await executor.run(code)
        print(f"Execution success: {success}, Output: {outputs}")
    print("Finish executing the loaded notebook")
    return executor

def clean_json_from_rsp(text):
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        json_str = "\n".join(matches)
        return json_str
    else:
        return ""
import os
import re
from datetime import datetime
from pathlib import Path

import nbformat
import yaml
from loguru import logger as _logger
from nbclient import NotebookClient
from nbformat.notebooknode import NotebookNode

from metagpt.roles.role import Role


def load_data_config(file_path="data.yaml"):
    with open(file_path, "r") as stream:
        data_config = yaml.safe_load(stream)
    return data_config


DATASET_CONFIG = load_data_config("datasets.yaml")
DATA_CONFIG = load_data_config()
DATA_CONFIG["datasets"] = DATASET_CONFIG["datasets"]


def get_mcts_logger():
    logfile_level = "DEBUG"
    name: str = None
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date  # name a log with prefix name

    # _logger.remove()
    _logger.level("MCTS", color="<green>", no=25)
    # _logger.add(sys.stderr, level=print_level)
    _logger.add(Path(DATA_CONFIG["work_dir"]) / DATA_CONFIG["role_dir"] / f"{log_name}.txt", level=logfile_level)
    _logger.propagate = False
    return _logger


mcts_logger = get_mcts_logger()


def get_exp_pool_path(task_name, data_config, pool_name="analysis_pool"):
    datasets_dir = data_config["datasets_dir"]
    if task_name in data_config["datasets"]:
        dataset = data_config["datasets"][task_name]
        data_path = os.path.join(datasets_dir, dataset["dataset"])
    else:
        raise ValueError(
            f"Dataset {task_name} not found in config file. Available datasets: {data_config['datasets'].keys()}"
        )
    exp_pool_path = os.path.join(data_path, f"{pool_name}.json")
    if not os.path.exists(exp_pool_path):
        return None
    return exp_pool_path


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


def save_notebook(role: Role, save_dir: str = "", name: str = "", save_to_depth=False):
    save_dir = Path(save_dir)
    tasks = role.planner.plan.tasks
    nb = process_cells(role.execute_code.nb)
    os.makedirs(save_dir, exist_ok=True)
    file_path = save_dir / f"{name}.ipynb"
    nbformat.write(nb, file_path)

    if save_to_depth:
        clean_file_path = save_dir / f"{name}_clean.ipynb"
        codes = [task.code for task in tasks if task.code]
        clean_nb = nbformat.v4.new_notebook()
        for code in codes:
            clean_nb.cells.append(nbformat.v4.new_code_cell(code))
        nbformat.write(clean_nb, clean_file_path)


async def load_execute_notebook(role):
    tasks = role.planner.plan.tasks
    codes = [task.code for task in tasks if task.code]
    executor = role.execute_code
    executor.nb = nbformat.v4.new_notebook()
    executor.nb_client = NotebookClient(executor.nb, timeout=role.role_timeout)
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

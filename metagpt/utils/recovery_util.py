# -*- coding: utf-8 -*-
# @Date    : 12/20/2023 11:07 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json
from datetime import datetime
from pathlib import Path

import nbformat

from metagpt.const import DATA_PATH
from metagpt.roles.role import Role
from metagpt.utils.common import read_json_file
from metagpt.utils.save_code import save_code_file


def load_history(save_dir: str = ""):
    """
    Load plan and code execution history from the specified save directory.

    Args:
        save_dir (str): The directory from which to load the history.

    Returns:
        Tuple: A tuple containing the loaded plan and notebook.
    """

    plan_path = Path(save_dir) / "plan.json"
    nb_path = Path(save_dir) / "history_nb" / "code.ipynb"
    plan = read_json_file(plan_path)
    nb = nbformat.read(open(nb_path, "r", encoding="utf-8"), as_version=nbformat.NO_CONVERT)
    return plan, nb


def save_history(role: Role, save_dir: str = ""):
    """
    Save plan and code execution history to the specified directory.

    Args:
        role (Role): The role containing the plan and execute_code attributes.
        save_dir (str): The directory to save the history.

    Returns:
        Path: The path to the saved history directory.
    """
    record_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_path = DATA_PATH / "output" / f"{record_time}"

    # overwrite exist trajectory
    save_path.mkdir(parents=True, exist_ok=True)

    plan = role.planner.plan.dict()

    with open(save_path / "plan.json", "w", encoding="utf-8") as plan_file:
        json.dump(plan, plan_file, indent=4, ensure_ascii=False)

    save_code_file(name=Path(record_time) / "history_nb", code_context=role.execute_code.nb, file_format="ipynb")
    return save_path

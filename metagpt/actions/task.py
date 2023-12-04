from typing import Dict


class Task:
    prompts: list[str]
    task_args_pool: list[Dict[str, str]]
    task_output_keys: list[str]

    def __init__(self, prompts: str, task_args_pool: list[Dict[str, str]], task_output_keys: list[str]):
        self.prompts = prompts
        self.task_args_pool = task_args_pool
        self.task_output_keys = task_output_keys
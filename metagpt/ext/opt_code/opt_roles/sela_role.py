# from metagpt.ext.opt_code.memory.sela_memory import SelaNode
from metagpt.ext.opt_code.opt_roles.experimenter import Experimenter
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.utils.common import read_json_file, write_json_file, CodeParser
from metagpt.logs import logger
from metagpt.tools.tool_recommend import ToolRecommender
from metagpt.schema import Message, Task, TaskResult
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.configs.llm_config import LLMConfig

import asyncio
import os
import json
from pathlib import Path
import nbformat
from nbformat.notebooknode import NotebookNode
from nbclient import NotebookClient
from pydantic import model_validator, BaseModel

CODE_BLOCK_RESULT = """
## Code:
{code}

## Execution Result:
{result}
"""

EXTRACT_SCORE_PROMPT = """
# Code Blocks
{code_block}
# Instruction:
Based on the code and execution result, please extract the **final scores** and return it as a dictionary.
If you cannot find the scores, please still return a dictionary with the keys 'train_score', 'dev_score', and 'test_score', and set the values to -1.

# Format:
```json
{{
    "train_score": x.x,
    "dev_score": x.x,
    "test_score": x.x
}}
```
"""

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

def save_notebook(role: 'SelaRole', save_dir: str = "", name: str = "", save_to_depth=False):
    save_dir = Path(save_dir)
    tasks = role.planner.plan.tasks
    nb = process_cells(role.execute_code.nb)
    os.makedirs(save_dir, exist_ok=True)
    file_path = save_dir / f"Node_{name}.ipynb"
    nbformat.write(nb, file_path)

    if save_to_depth:
        clean_file_path = save_dir / f"{name}_clean.ipynb"
        codes = [task.code for task in tasks if task.code]
        clean_nb = nbformat.v4.new_notebook()
        for code in codes:
            clean_nb.cells.append(nbformat.v4.new_code_cell(code))
        nbformat.write(clean_nb, clean_file_path)

def async_timeout():
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            try:
                result = await asyncio.wait_for(func(self, *args, **kwargs), timeout=self.role_timeout)
            except asyncio.TimeoutError:
                text = f"Function timed out after {self.role_timeout} seconds"
                logger.error(text)
                self.save_state()
                raise TimeoutException(text)
            return result
        return wrapper
    return decorator

class TimeoutException(Exception):
    pass

class SelaRole(DataInterpreter, Experimenter): # TODO 现在继承 Experimenter 有 Bug
    llm_config: LLMConfig = None
    start_task_id: int = 1
    node_id: str = ""
    role_timeout: int = 1000
    if_start: bool = False
    state_saved: bool = False
    root_path: str = "metagpt/ext/opt_code/optimized/titanic/sela/roles" # TODO fix this

    async def initialize(self, node, kwargs: dict, root_path):
        # self.root_path = root_path
        self.args = kwargs
        self.llm_config = kwargs["llm_config"]
        self.llm = create_llm_instance(kwargs["llm_config"])
        return await self.run(node)
    
    @model_validator(mode="after")
    def set_plan_and_tool(self):
        if self.planner.plan.goal != "":
            self.set_actions([WriteAnalysisCode])
            self._set_state(0)
            print("Plan already exists, skipping initialization.")
            return self
        print("Initializing plan and tool...")
        return super().set_plan_and_tool()
    
    async def _act_on_task(self, current_task: Task) -> TaskResult:
        """Useful in 'plan_and_act' mode. Wrap the output in a TaskResult for review and confirmation."""
        code, result, is_success = await self._write_and_exec_code()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        if int(current_task.task_id) == self.start_task_id + 1:
            # fe_id = current_task.dependent_task_ids
            self.save_state() # TODO save state
            save_notebook(role=self, save_dir=self.root_path, name=self.node_id, save_to_depth=True)
        else:
            save_notebook(role=self, save_dir=self.root_path, name=self.node_id)
        return task_result

    def save_state(self, static_save=False):
        """
        attribute:
            state_saved - the state has been saved
        input:
            static_save - saving the state without changing the state_saved flag - used when a new role is created
        """
        if self.state_saved and not static_save:
            return
        if not static_save:
            self.state_saved = True

        stg_path = self.root_path
        name = self.node_id
        role_path = os.path.join(stg_path, f"Node_{name}.json")
        # save state as json file
        write_json_file(role_path, self.model_dump())

    def change_next_instruction(self, new_instruction):
        if new_instruction is not None:
            self.planner.plan.task_map[str(self.start_task_id)].instruction = new_instruction
            self.remap_tasks()

    def remap_tasks(self):
        self.planner.plan.tasks = [
            self.planner.plan.task_map[task_id] for task_id in sorted(self.planner.plan.task_map.keys())
        ]

    def load_state(self, node): # TODO 应该放到 Node 类中
        stg_path = self.root_path
        name = node.id
        role_dict = read_json_file(os.path.join(stg_path, f"Node_{name}.json"))
        if role_dict.get("tool_recommender") is None:
            role_dict["tool_recommender"] = ToolRecommender()
        elif isinstance(role_dict.get("tool_recommender", {}).get("tools"), dict):
            role_dict["tool_recommender"]["tools"] = list(role_dict["tool_recommender"]["tools"].keys())

        role_dict["llm_config"]["region_name"] = ""
        self.__init__(**role_dict) #TODO check

        if node.parent is not None:
            parent_role = SelaRole().load_state(node.parent)
            self.update_til_start_task(parent_role, backward=False)

        self.remap_tasks()
        self.llm = create_llm_instance(self.llm_config)
        return self
    
    def update_til_start_task(self, role: 'SelaRole', backward=True): 
        if backward:
            # make sure the previous task instructions are matched
            assert (
                self.start_task_id == role.start_task_id - 1
            ), f"start_task_id: {self.start_task_id}, role.start_task_id: {role.start_task_id}"
            for i in range(self.start_task_id):
                if (
                    self.planner.plan.task_map[str(self.start_task_id)].instruction
                    != role.planner.plan.task_map[str(self.start_task_id)].instruction
                ):
                    logger.info("Previous task instructions not matched")
                    self.remap_tasks()
                    return
            # copy new role's task (self.start_task_id) to current role
            self.planner.plan.task_map[str(self.start_task_id)] = role.planner.plan.task_map[
                str(self.start_task_id)
            ].model_copy()
            self.remap_tasks()
        else:
            assert (
                self.start_task_id == role.start_task_id + 1
            ), f"start_task_id: {self.start_task_id}, parent_role.start_task_id: {role.start_task_id}"

            if int(role.planner.plan.current_task_id) > self.start_task_id:
                for i in range(role.start_task_id):
                    self.planner.plan.task_map[str(i)] = role.planner.plan.task_map[str(i)].model_copy()
            self.remap_tasks()
    
    async def load_execute_notebook(self):
        tasks = self.planner.plan.tasks
        codes = [task.code for task in tasks if task.code]
        executor = self.execute_code
        executor.nb = nbformat.v4.new_notebook()
        executor.nb_client = NotebookClient(executor.nb, timeout=self.role_timeout)
        # await executor.build()
        for code in codes:
            outputs, success = await executor.run(code)
            print(f"Execution success: {success}, Output: {outputs}")
        print("Finish executing the loaded notebook")
        return executor
    
    async def get_score(self):
        score_dict = await self.llm_extract_score()
        score_dict["score"] = score_dict["dev_score"]
        return score_dict
    
    async def llm_extract_score(self):
        num_tasks = len(self.planner.plan.task_map)
        task_map = self.planner.plan.task_map
        code_block = "\n".join(
            [
                CODE_BLOCK_RESULT.format(code=task_map[str(i + 1)].code, result=task_map[str(i + 1)].result)
                for i in range(num_tasks)
            ]
        )
        rsp = await self.llm.aask(EXTRACT_SCORE_PROMPT.format(code_block=code_block, role="user"))
        json_block = CodeParser.parse_code(block=None, text=rsp)
        score_dict = json.loads(json_block)
        return score_dict
        
    async def run(self, node, context = None, kwargs = None):       
        max_retries = 3
        num_runs = 1
        run_finished = False
        while num_runs <= max_retries and not run_finished:
            try:
                if self.if_start:
                    self.load_state(node) #TODO load state
                    await self.load_execute_notebook()
                    await DataInterpreter.run(self, with_message="continue")
                else:
                    await DataInterpreter.run(self, with_message=node.state["requirement"])
                    self.if_start = True

                score_dict = await self.get_score()
                score_dict = node.evaluate_simulation(score_dict)
                node.raw_reward = score_dict
                run_finished = True
            except TimeoutException as e:
                break
            except Exception as e:
                print(f"Error: {e} when running node {node.id}")
                num_runs += 1
            
        if not run_finished:
            score_dict = {"test_score": 0, "dev_score": 0, "score": 0}

            node.raw_reward = score_dict

        if node.state["low_is_better"]:
            def normalize_score(score):
                if score == -1:
                    return 0
                return 1 / (1 + score)
            
            score_dict = {k: normalize_score(v) for k, v in score_dict.items()}

        node.normalized_reward = score_dict
        self.update_node(node) # TODO
        
        return score_dict
    
    def update_node(self, node):
        codes = [task.code for task in self.planner.plan.tasks]
        outputs = [task.result for task in self.planner.plan.tasks]
        
        node.tasks = self.planner.plan.tasks
        node.code = codes
        node.outputs = outputs
    
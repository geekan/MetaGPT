import json
from datetime import datetime

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.ask_review import ReviewConst
from metagpt.actions.write_analysis_code import WriteCodeByGenerate
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.utils.save_code import save_code_file


class CodeInterpreter(Role):
    def __init__(
        self, name="Charlie", profile="CodeInterpreter", goal="", auto_run=False, use_tools=False,
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act", auto_run=auto_run, use_tools=use_tools)
        self.execute_code = ExecutePyCode()

    @property
    def working_memory(self):
        return self._rc.working_memory
    
    async def _plan_and_act(self):

        rsp = await super()._plan_and_act()

        # save code using datetime.now or keywords related to the goal of your project (plan.goal).
        project_record = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_code_file(name=project_record, code_context=self.execute_code.nb, file_format="ipynb")

        return rsp
    
    async def _act_on_task(self, current_task: Task) -> TaskResult:
        code, result, is_success = await self._write_and_exec_code()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        return task_result

    async def _write_and_exec_code(self, max_retry: int = 3):
        
        counter = 0
        success = False
        
        while not success and counter < max_retry:
            context = self.planner.get_useful_memories()

            logger.info("Write code with pure generation")

            code = await WriteCodeByGenerate().run(
                context=context, plan=self.planner.plan, temperature=0.0
            )
            cause_by = WriteCodeByGenerate

            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )
            
            result, success = await self.execute_code.run(code)
            print(result)

            self.working_memory.add(
                Message(content=result, role="user", cause_by=ExecutePyCode)
            )
            
            if "!pip" in code:
                success = False
            
            counter += 1
            
            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD[0] in review:
                    counter = 0  # redo the task again with help of human suggestions
        
        return code, result, success

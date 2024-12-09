from __future__ import annotations

import json
from typing import Literal

from pydantic import Field, model_validator
from metagpt.gui_update_callback import gui_update_callback

from metagpt.actions.di.ask_review import ReviewConst
from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import CheckData, WriteAnalysisCode
from metagpt.logs import logger
from metagpt.prompts.di.write_analysis_code import DATA_INFO
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.strategy.task_type import TaskType
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.utils.common import CodeParser

REACT_THINK_PROMPT = """
# User Requirement
{user_requirement}
# Context
{context}

Output a json following the format:
```json
{{
    "thoughts": str = "Thoughts on current situation, reflect on how you should proceed to fulfill the user requirement",
    "state": bool = "Decide whether you need to take more actions to complete the user requirement. Return true if you think so. Return false if you think the requirement has been completely fulfilled."
}}
```
"""


class DataInterpreter(Role):
    name: str = "David"
    profile: str = "DataInterpreter"
    auto_run: bool = True
    use_plan: bool = True
    use_reflection: bool = False
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)
    tools: list[str] = []  # Use special symbol ["<all>"] to indicate use of all registered tools
    tool_recommender: ToolRecommender = None
    react_mode: Literal["plan_and_act", "react"] = "plan_and_act"
    max_react_loop: int = 10  # used for react mode

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "DataInterpreter":
        logger.info(f"Initializing DataInterpreter: {self.name} with profile: {self.profile}")
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop, auto_run=self.auto_run)
        logger.debug(f"React mode set to: {self.react_mode}, max react loop: {self.max_react_loop}")
        self.use_plan = (
            self.react_mode == "plan_and_act"
        )  # create a flag for convenience, overwrite any passed-in value
        if self.tools and not self.tool_recommender:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools)
        self.set_actions([WriteAnalysisCode])
        self._set_state(0)
        return self

    @property
    def working_memory(self):
        return self.rc.working_memory

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        logger.info("===> Thinking about the next action.")
        user_requirement = self.get_memories()[0].content
        logger.debug(f"User requirement: {user_requirement}")
        context = self.working_memory.get()
        logger.debug(f"Current context: {context}")

        if not context:
            # just started the run, we need action certainly
            logger.info("===> Starting new run, adding user requirement to working memory.")
            self.working_memory.add(self.get_memories()[0])  # add user requirement to working memory
            self._set_state(0)
            return True

        prompt = REACT_THINK_PROMPT.format(user_requirement=user_requirement, context=context)
        logger.debug("Sending prompt to LLM for response.")
        rsp = await self.llm.aask(prompt)
        logger.debug(f"Received response: {rsp}")
        rsp_dict = json.loads(CodeParser.parse_code(block=None, text=rsp))
        self.working_memory.add(Message(content=rsp_dict["thoughts"], role="assistant"))
        need_action = rsp_dict["state"]
        self._set_state(0) if need_action else self._set_state(-1)

        return need_action

    async def _act(self) -> Message:
        """Useful in 'react' mode. Return a Message conforming to Role._act interface."""
        logger.info("===> Acting based on the current task.")
        code, _, _ = await self._write_and_exec_code()
        logger.debug(f"Generated code: {code}")
        return Message(content=code, role="assistant", cause_by=WriteAnalysisCode)

    async def _plan_and_act(self) -> Message:
        try:
            logger.info("===> Planning and acting on the task.")
            if self.update_callback:
                update_info = {
                    "event": "plan_and_act_started",
                    "status": "Starting plan and act execution",
                    "current_task": None,
                    "progress": 0
                }
                await self.update_callback(update_info)
                await gui_update_callback(update_info)
            
            rsp = await super()._plan_and_act()
            logger.info("===> Terminating code execution.")
            await self.execute_code.terminate()
            
            if self.update_callback:
                update_info = {
                    "event": "plan_and_act_completed",
                    "status": "Completed plan and act execution",
                    "response": str(rsp),
                    "progress": 100
                }
                await self.update_callback(update_info)
                await gui_update_callback(update_info)
            
            logger.info(f"Plan and act response: {rsp}")
            return rsp
        except Exception as e:
            await self.execute_code.terminate()
            raise e

    async def _act_on_task(self, current_task: Task) -> TaskResult:
        """Useful in 'plan_and_act' mode. Wrap the output in a TaskResult for review and confirmation."""
        code, result, is_success = await self._write_and_exec_code()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        return task_result

    async def _write_and_exec_code(self, max_retry: int = 3):
        if self.update_callback:
            await self.update_callback({
                "event": "acting",
                "action": "write_and_exec_code",
                "description": "Starting code writing and execution",
                "action_details": {"max_retry": max_retry}
            })
            await gui_update_callback({
                "event": "acting",
                "action": "write_and_exec_code",
                "description": "Starting code writing and execution",
                "action_details": {"max_retry": max_retry}
            })
            
        logger.info("===> Writing and executing code.")
        counter = 0
        logger.debug(f"Max retry attempts: {max_retry}")
        success = False

        # plan info
        plan_status = self.planner.get_plan_status() if self.use_plan else ""
        logger.debug(f"Plan status: {plan_status}")

        # tool info
        if self.tool_recommender:
            context = (
                self.working_memory.get()[-1].content if self.working_memory.get() else ""
            )  # thoughts from _think stage in 'react' mode
            plan = self.planner.plan if self.use_plan else None
            tool_info = await self.tool_recommender.get_recommended_tool_info(context=context, plan=plan)
        else:
            tool_info = ""

        # data info
        logger.info("===> Checking data before execution.")
        await self._check_data()

        while not success and counter < max_retry:
            ### write code ###
            if self.update_callback:
                self.update_callback({
                    "event": "acting",
                    "action": "writing_code",
                    "description": f"Attempt {counter + 1} of {max_retry}",
                    "action_details": {"attempt": counter + 1}
                })
                
            code, cause_by = await self._write_code(counter, plan_status, tool_info)
            logger.info(f"Attempt {counter + 1}: Writing code.")
            self.working_memory.add(Message(content=code, role="assistant", cause_by=cause_by))
            logger.debug(f"Code written: {code}")

            ### execute code ###
            if self.update_callback:
                self.update_callback({
                    "event": "acting",
                    "action": "executing_code",
                    "description": "Executing generated code",
                    "action_details": {"code_length": len(code)}
                })
                
            logger.info("===> Executing code.")
            result, success = await self.execute_code.run(code)
            logger.debug(f"Execution result: {result}, success: {success}")
            print(result)

            self.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1

            if not success and counter >= max_retry:
                logger.info("===> coding failed!")
                logger.info("===> Code execution failed, requesting review.")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                logger.debug(f"Review response: {review}")
                if ReviewConst.CHANGE_WORDS[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        task_result = TaskResult(code=code, result=result, is_success=success)
        return code, result, success

    async def _write_code(
        self,
        counter: int,
        plan_status: str = "",
        tool_info: str = "",
    ):
        todo = self.rc.todo  # todo is WriteAnalysisCode
        logger.info(f"ready to {todo.name}")
        use_reflection = counter > 0 and self.use_reflection  # only use reflection after the first trial

        user_requirement = self.get_memories()[0].content

        code = await todo.run(
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info,
            working_memory=self.working_memory.get(),
            use_reflection=use_reflection,
        )

        return code, todo

    async def _check_data(self):
        if (
            not self.use_plan
            or not self.planner.plan.get_finished_tasks()
            or self.planner.plan.current_task.task_type
            not in [
                TaskType.DATA_PREPROCESS.type_name,
                TaskType.FEATURE_ENGINEERING.type_name,
                TaskType.MODEL_TRAIN.type_name,
            ]
        ):
            return
        logger.info("===> Check updated data")
        code = await CheckData().run(self.planner.plan)
        if not code.strip():
            return
        result, success = await self.execute_code.run(code)
        if success:
            print(result)
            data_info = DATA_INFO.format(info=result)
            self.working_memory.add(Message(content=data_info, role="user", cause_by=CheckData))

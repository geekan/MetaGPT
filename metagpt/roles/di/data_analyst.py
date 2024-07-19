from __future__ import annotations

import re
from typing import List

from pydantic import Field, model_validator

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.logs import logger
from metagpt.prompts.di.data_analyst import EXTRA_INSTRUCTION, TASK_TYPE_DESC, CODE_STATUS, BROWSER_INFO
from metagpt.prompts.di.role_zero import ROLE_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import TaskResult, Message
from metagpt.strategy.experience_retriever import ExpRetriever, KeywordExpRetriever
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool


@register_tool(include_functions=["write_and_exec_code"])
class DataAnalyst(RoleZero):
    name: str = "David"
    profile: str = "DataAnalyst"
    goal: str = "Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web searching, web deployment, terminal operation, git and github operation, etc."
    instruction: str = ROLE_INSTRUCTION + EXTRA_INSTRUCTION
    task_type_desc: str = TASK_TYPE_DESC

    tools: list[str] = ["Plan", "DataAnalyst", "RoleZero", "Browser"]
    custom_tools: list[str] = ["machine learning", "web scraping", "Terminal"]
    custom_tool_recommender: ToolRecommender = None
    experience_retriever: ExpRetriever = KeywordExpRetriever()

    use_reflection: bool = True
    write_code: WriteAnalysisCode = Field(default_factory=WriteAnalysisCode, exclude=True)
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)

    @model_validator(mode="after")
    def set_custom_tool(self):
        if self.custom_tools and not self.custom_tool_recommender:
            self.custom_tool_recommender = BM25ToolRecommender(tools=self.custom_tools)

    def _update_tool_execution(self):
        self.tool_execution_map.update({
            "DataAnalyst.write_and_exec_code": self.write_and_exec_code,
        })

    async def parse_browser_actions(self, memory: List[Message]) -> List[Message]:
        memory = await super().parse_browser_actions(memory)
        browser_actions = []
        for index, msg in enumerate(memory):
            if msg.cause_by == "browser":
                browser_url = re.search('URL: (.*?)\\n', msg.content).group(1)
                pattern = re.compile(r"Command Browser\.(\w+) executed")
                browser_actions.append({
                    'command': pattern.match(memory[index - 1].content).group(1),
                    'current url': browser_url
                })
        if browser_actions:
            browser_actions = BROWSER_INFO.format(browser_actions=browser_actions)
            self.rc.working_memory.add(Message(content=browser_actions, role="user", cause_by="browser"))
        return memory

    async def write_and_exec_code(self, instruction: str = ""):
        """Write a code block for current task and execute it in an interactive notebook environment.

        Args:
            instruction: The specific task description for which the code needs to be written.
        """
        counter = 0
        success = False
        await self.execute_code.init_code()

        # plan info
        plan_status = self.planner.get_plan_status()
        plan_status = plan_status + f"\nFurther Task Instruction: {instruction}"

        # tool info
        if self.custom_tool_recommender:
            plan = self.planner.plan
            fixed = ["Terminal"] if "Terminal" in self.custom_tools else None
            tool_info = await self.custom_tool_recommender.get_recommended_tool_info(fixed=fixed, plan=plan)
        else:
            tool_info = ""

        while not success and counter < 3:
            ### write code ###
            logger.info(f"ready to WriteAnalysisCode")
            use_reflection = (counter > 0 and self.use_reflection)  # only use reflection after the first trial

            code = await self.write_code.run(
                user_requirement=self.planner.plan.goal,
                plan_status=plan_status,
                tool_info=tool_info,
                working_memory=self.rc.working_memory.get(),
                use_reflection=use_reflection,
            )
            self.rc.working_memory.add(Message(content=code, role="assistant", cause_by=WriteAnalysisCode))

            ### execute code ###
            result, success = await self.execute_code.run(code)
            print(result)

            self.rc.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1
            if success:
                task_result = TaskResult(code=code, result=result, is_success=success)
                self.planner.current_task.update_task_result(task_result)

        status = 'Success' if success else 'Failed'
        output = CODE_STATUS.format(code=code, status=status, result=result)
        if success:
            output += 'The code written has been executed successfully.'
        self.rc.working_memory.clear()
        return output

from __future__ import annotations

from pydantic import Field, model_validator

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.logs import logger
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import TaskResult, Message
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool


@register_tool(include_functions=["write_and_exec_code"])
class DataAnalyst(RoleZero):
    name: str = "David"
    profile: str = "DataAnalyst"
    goal: str = "Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web searching, web deployment, terminal operation, git and github operation, etc."

    tools: list[str] = ["Plan", "DataAnalyst", "RoleZero"]
    custom_tools: list[str] = ["machine learning", "web scraping", "Terminal"]
    custom_tool_recommender: ToolRecommender = None

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

    async def write_and_exec_code(self):
        """Write a code block for current task and execute it in an interactive notebook environment."""
        counter = 0
        success = False
        await self.execute_code._init_code()

        # plan info
        plan_status = self.planner.get_plan_status()

        # tool info
        if self.custom_tool_recommender:
            plan = self.planner.plan
            fix = ["Terminal"] if "Terminal" in self.custom_tools else None
            tool_info = await self.custom_tool_recommender.get_recommended_tool_info(fix=fix, plan=plan)
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
                working_memory=self.rc.working_memory.get() if use_reflection else None,
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
        output = f"""
        **Code written**:
        {code}
        **Execution status**:{'Success' if success else 'Failed'}
        **Execution result**: {result}
        """
        self.rc.working_memory.clear()
        return output

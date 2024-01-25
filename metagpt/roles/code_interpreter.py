from pydantic import Field

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.write_and_execute_code import WriteAndExecuteCode
from metagpt.logs import logger
from metagpt.roles import Role


class CodeInterpreter(Role):
    execute_code: ExecutePyCode = Field(
        default_factory=ExecutePyCode, exclude=True
    )  # code execution environment must be at the role level for each of its actions to share

    def __init__(
        self,
        name="Charlie",
        profile="CodeInterpreter",
        goal="",
        auto_run=True,
        use_tools=False,
        tools=[],
        **kwargs,
    ):
        super().__init__(name=name, profile=profile, goal=goal, use_plan=True, **kwargs)
        if use_tools and tools:
            from metagpt.tools.tool_registry import (
                validate_tool_names,  # import upon use
            )

            tools = validate_tool_names(tools)
            logger.info(f"will only use {tools} as tools")

        actions = [
            {
                "class": WriteAndExecuteCode,
                "args": {
                    "name": "WriteAndExecuteCode",
                    "desc": "For writing and executing codes to solve a task",
                    "use_tools": use_tools,
                    "tools": tools,
                    "execute_code": self.execute_code,
                },
            },
        ]
        self.set_planner(auto_run=auto_run, use_tools=use_tools, actions=actions)

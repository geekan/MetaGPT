from pydantic import Field

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.write_analysis_code import (
    MakeTools,
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.utils.common import remove_comments


class ToolMaker(Role):
    execute_code: ExecutePyCode = Field(default_factory=ExecutePyCode, exclude=True)

    async def make_tool(self, code: str, instruction: str, task_id: str = ""):
        if len(remove_comments(code).split("\n")) < 5:  # no need to consider trivial codes with fewer than 5 lines
            return

        logger.warning(
            f"Making tools for task_id {task_id}: \
            `{instruction}` \n code: \n {code}"
        )
        make_tools = MakeTools()
        make_tool_retries, make_tool_current_retry = 3, 0
        while True:
            # start make tools
            tool_code = await make_tools.run(code, instruction)
            make_tool_current_retry += 1

            # check tool_code by execute_code
            logger.info(f"Checking task_id {task_id} tool code by executor...")
            execute_result, execute_success = await self.execute_code.run(tool_code)
            if not execute_success:
                logger.error(f"Tool code faild to execute, \n{execute_result}\n.We will try to fix it ...")
            # end make tools
            if execute_success or make_tool_current_retry >= make_tool_retries:
                if make_tool_current_retry >= make_tool_retries:
                    logger.error(
                        f"We have tried the maximum number of attempts {make_tool_retries}\
                        and still have not created tools for task_id {task_id} successfully,\
                            we will skip it."
                    )
                break
        # save successful tool code in udf
        if execute_success:
            make_tools.save(tool_code)

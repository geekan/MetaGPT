# -*- coding: utf-8 -*-
# @Date    : 1/11/2024 7:06 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio
from metagpt.const import METAGPT_ROOT
from metagpt.actions.write_analysis_code import WriteCodeWithTools
from metagpt.plan.planner import Planner
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.roles.code_interpreter import CodeInterpreter

sd_url = 'http://106.75.10.65:19094/sdapi/v1/txt2img'
requirement = f"i have a text2image tool, generate a girl image use it, sd_url={sd_url}"

if __name__ == "__main__":
    code_interpreter = CodeInterpreter(use_tools=True, goal=requirement)
    asyncio.run(code_interpreter.run(requirement))
    # planner = Planner(
    #     goal="i have a sdt2i tool, generate a girl image use it, sd_url='http://106.75.10.65:19094/sdapi/v1/txt2img'",
    #     auto_run=True)
    # asyncio.run(planner.update_plan())

# schema_path = METAGPT_ROOT / "metagpt/tools/functions/schemas"
# #
# prompt = "1girl,  beautiful"
# planner = Planner(
#     goal="i have a sdt2i tool, generate a girl image use it, sd_url='http://106.75.10.65:19094/sdapi/v1/txt2img'",
#     auto_run=True)
# asyncio.run(planner.update_plan())
# planner.plan.current_task.task_type = "sd"
# planner.plan.current_task.instruction = "Use the sdt2i tool with the provided API endpoint to generate the girl image."
# executor = ExecutePyCode()
#
# tool_context, code = asyncio.run(WriteCodeWithTools(schema_path=schema_path).run(
#                     context=f"task prompt: {prompt}",
#                     plan=planner.plan,
#                     column_info="",
#                 ))
# print(code)
# asyncio.run(executor.run(code))

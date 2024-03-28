# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import re
from typing import Literal, Union

from metagpt.actions.di.ask_review import ReviewConst
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message

IDENTIFY_LINE_RANGES_REQUIREMENT = """
# Instruction
Identify the code files to be modified and their line ranges, provided python dict, in the provided <code>code</code> blocks based on the given <issue>issue</issue> in the Issues and Codes containing accessible code files with {script_names}. If the code is extremely long, focus on the <issue>issue</issue> description to narrow down the areas of concern. The line ranges should be within 50-300 lines and there may be more than one range in every files.

# Think about it by following these steps:
1. Identify the files containing errors based on the <issue>issue</issue> by using a single class or function as the basic unit of investigation.
2. For each identified file:
   a. Locate the relevant code section(s) based on the <issue>issue</issue> description.
   b. Determine the line range(s) within those code sections that need to be modified.
   c. Ensure the line range(s) fall within the 50-300 line limit, adjusting as necessary.
3. Output the code files to be modified and line ranges as a dict.

# Examples:
1. If file1.py has an error in a specific function with line ranges 20-50, output dict: 
```python
{{"file1.py":["20-50"]}}
```
2. If file1.py have errors in different functions with line ranges 20-50 and 100-120 respectively, output dict: 
```python
{{"file1.py":["20-50", "100-120"]}}
```
3. If file1.py has an error in a specific function with line ranges 20-50, and file2.py have errors in different functions with line ranges 20-50 and 100-120 respectively, output dict: 
```python
{{"file1.py":["20-50"], "file2.py":["20-50", "100-120"]}}
```

# Issues and Codes
{issues_and_codes}
"""


class GitAgent(DataInterpreter):
    name: str = "Jacky"
    profile: str = "Solve git issues proficiently"
    auto_run: bool = True
    use_plan: bool = True
    use_reflection: bool = False
    react_mode: Literal["plan_and_act", "react"] = "react"
    script_names: Union[str, list[str]] = []
    instance_id: str = ""

    async def critique(self, result, review_format):
        review_result = (
            "Finally, return a boolean value (True or False) to indicate the result of the review. "
            "Note: If the result is good enough, return True; otherwise, return False."
        )
        status = await self.llm.aask(
            [
                Message(content=review_format, role="user"),
                Message(content=result, role="assistant"),
                Message(content=review_result, role="user"),
            ]
        )
        logger.info(status)

        return status

    async def review_patch(self, code):
        review_format = (
            "Please ensure that the code {code} and original script {original_script} can fix the issue {memory} in patch format. "
            "If it is not in patch format, please convert it to patch format."
        )

        results = []
        for script in self.script_names:
            with open(script, "r", encoding="utf-8") as fp:
                original_script = fp.read()

            memory = self.get_memories()[0].content
            review_prompt = review_format.format(code=code, original_script=original_script, memory=memory)
            # todo: extract issue and remove image urls
            result = await self.llm.aask(review_prompt)

            results.append(result)
        # fixme: merge results to a single patch file
        result = "\n".join(results)

        return result, review_prompt

    async def _write_and_exec_code(self, max_retry: int = 3):
        counter = 0
        success = False

        # plan info
        plan_status = self.planner.get_plan_status() if self.use_plan else ""

        # tool info
        if self.tools:
            context = (
                self.working_memory.get()[-1].content if self.working_memory.get() else ""
            )  # thoughts from _think stage in 'react' mode
            plan = self.planner.plan if self.use_plan else None
            tool_info = await self.tool_recommender.get_recommended_tool_info(context=context, plan=plan)
        else:
            tool_info = ""

        while not success and counter < max_retry:
            ### write code ###
            code, cause_by = await self._write_code(counter, plan_status, tool_info)

            self.working_memory.add(Message(content=code, role="assistant", cause_by=cause_by))

            result, format_prompt = await self.review_patch(code)

            success = await self.critique(result, format_prompt)
            # success = True
            await self.execute_code.run(code)
            ### execute code ###
            # todo: execute: git apply

            ### process execution result ###
            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORDS[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        return code, result, success

    # TODO retry 3 times
    async def identify_line_ranges(self, script_names, issues_and_codes):
        prompt = IDENTIFY_LINE_RANGES_REQUIREMENT.format(script_names=script_names, issues_and_codes=issues_and_codes)
        lines_rsp = await self.llm.aask(prompt)
        match = re.search(r'python\s*(\{.*?\})\s*', lines_rsp, re.DOTALL)
        lines = eval(match.group(1)) if match else {}
        return lines

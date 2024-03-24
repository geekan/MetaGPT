# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import re
from typing import Literal, Union

from metagpt.actions import ExecuteNbCode
from metagpt.actions.di.ask_review import ReviewConst
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message
from metagpt.utils.common import CodeParser

CODE_AND_TEST_CODE_SPLIT_SYMBOL = "#†††#"

WRITE_TEST_CODE_PROMPT = """
NOTICE
1. Role: You are a QA engineer; the main goal is to design, develop, and execute PEP8 compliant, well-structured, maintainable test cases and scripts in jupyter notebook. Your focus should be on ensuring the product quality of the entire project through systematic testing.
2. Requirement: Based on the context, develop a comprehensive test suite that adequately covers all relevant aspects of the code file under review. Your test suite will be part of the overall project QA, so please develop complete, robust, and reusable test cases.
3. Attention1: Use '##' to split sections, not '#'.
4. Attention2: If there are any settings in your tests, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
5. Attention3: you should correctly use existing variable, instantiate classes or import the necessary classes in test code. 
6. Think before writing: What should be tested and validated in this document? What edge cases could exist? What might fail?
7. CAREFULLY CHECK THAT YOU DON'T MISS ANY NECESSARY TEST CASES and DON'T OMIT THE IMPLEMENTATION OF TEST CODE.
8. When writing the main function that includes the `argv` and `exit` parameters for executing unit tests, use unittest.main(argv=[''], exit=False) for no command-line arguments, or unittest.main(argv=['arg'], exit=False) with 'arg' replaced by the desired argument value.
-----
## Given the code context to test and precious implementation in jupyter notebook, please write appropriate test cases using Python's unittest framework to verify the correctness and robustness of this code:

## Code Context To Test
{code_to_test}

## Precious Implementation
{previous_impl}
"""

GET_LINES_REQUIREMENT = """
# Instruction
Identify the line ranges of the errant code snippets in the provided <code>code</code> blocks based on the given <issue>issue</issue>. If the code is extremely long, focus on the <issue>issue</issue> description to narrow down the areas of concern. The line ranges, provided a list, should be within 50-200 lines and there may be more than one range. In case of uncertainty, output a list containing as many potentially relevant ranges as possible.

# Think about it by following these steps:
1. Identify the files containing errors based on the <issue>issue</issue>.
2. For each identified file:
   a. Locate the relevant code section(s) based on the <issue>issue</issue> description.
   b. Determine the line range(s) within those code sections that need to be modified.
   c. Ensure the line range(s) fall within the 0-200 line limit, adjusting as necessary.
3. Output the line ranges as a list.

# Examples:
1. If file1.py has an error in a specific function, and the line range to be modified is 20-50, output list: ["20-50"]
2. If file1.py have errors in different functions with line ranges 20-50 and 100-120 respectively, output list: ["20-50", "100-120"]
3. If file1.py has potential errors, but the exact nature and locations of the errors are uncertain, and the code of file1.py has 200 lines in total, output list: ["0-200"]

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

            ### write test code ###
            test_code = await self._write_test_code(code)

            code_and_test_code = code + f"\n{CODE_AND_TEST_CODE_SPLIT_SYMBOL}\n" + test_code

            self.working_memory.add(Message(content=code_and_test_code, role="assistant", cause_by=cause_by))
            result, success = await self.execute_code.run(code_and_test_code)
            self.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            result, format_prompt = await self.review_patch(code)

            success = await self.critique(result, format_prompt)
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

    async def _write_test_code(self, code: str):
        logger.info("ready to write test code")
        prompt = WRITE_TEST_CODE_PROMPT.format(
            code_to_test=code,
            previous_impl=self.working_memory.get(),
        )
        code_rsp = await self.llm.aask(prompt)

        try:
            test_code = CodeParser.parse_code(block="", text=code_rsp)
        except Exception:
            # Handle the exception if needed
            logger.error(f"Can't parse the code: {code_rsp}")

            # Return code_rsp in case of an exception, assuming llm just returns code as it is and doesn't wrap it inside ```
            test_code = code_rsp
        return test_code

    async def identify_line_ranges(self, issues_and_codes):
        prompt = GET_LINES_REQUIREMENT.format(issues_and_codes=issues_and_codes)
        lines_rsp = await self.llm.aask(prompt)

        try:
            lines = re.findall(r'\["([\d-]+)"\]', lines_rsp)
        except Exception:
            # Handle the exception if needed
            logger.error(f"Can't parse the list: {lines_rsp}")
            lines = lines_rsp
        return lines

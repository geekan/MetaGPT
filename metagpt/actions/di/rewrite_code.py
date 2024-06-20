import os

from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action import Action
from metagpt.actions.write_code_review import (
    EXAMPLE_AND_INSTRUCTION,
    FORMAT_EXAMPLE,
    PROMPT_TEMPLATE,
    REWRITE_CODE_TEMPLATE,
)
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, aread, awrite


@register_tool(tags=["RewriteCode"], include_functions=["run"])
class RewriteCode(Action):
    """Accordding design doc and task doc to review the code, to make the complete and correct code."""

    name: str = "RewriteCode"

    async def run(
        self, code_path: str, design_doc_input: str = "", task_doc_input: str = "", code_review_k_times: int = 2
    ) -> str:
        """Reviews the provided code based on the accompanying design and task documentation, return the complete and correct code.

        Read the code from `code_path`, and write the final code to `code_path`.
        If there is no `design_doc_input` or `task_doc_input`, it will return and do nothing.

        Args:
            code_path (str): The file path of the code snippet to be reviewed. This should be a string containing the path to the source code file.
            design_doc_input (str): Content or file path of the design document associated with the code. This should describe the system architecture, used in the code. It helps provide context for the review process.
            task_doc_input (str): Content or file path of the task document describing what the code is intended to accomplish. This should outline the functional requirements or objectives of the code.
            code_review_k_times (int, optional): The number of iterations for reviewing and potentially rewriting the code. Defaults to 2.

        Returns:
            str: The potentially corrected or approved code after review.

        Example Usage:
            # Example of how to call the run method with a code snippet and documentation
            await WriteCodeReview().run(
                code_path="/tmp/game.js",
                design_doc_input="/tmp/design_doc.json",
                task_doc_input='{"Required packages":["No third-party dependencies required"], ...}'
            )
        """
        if not design_doc_input or not task_doc_input:
            return

        code = await aread(code_path)

        # Check if design_doc_input and task_doc_input are paths or content, and read if they are paths
        if os.path.exists(design_doc_input):
            logger.info(f"read from {design_doc_input}")
            design_doc_input = await aread(design_doc_input)

        if os.path.exists(task_doc_input):
            logger.info(f"read from {task_doc_input}")
            task_doc_input = await aread(task_doc_input)

        context = "\n".join(
            [
                "## System Design\n" + design_doc_input + "\n",
                "## Task\n" + task_doc_input + "\n",
            ]
        )

        for i in range(code_review_k_times):
            context_prompt = PROMPT_TEMPLATE.format(context=context, code=code, filename=code_path)
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=FORMAT_EXAMPLE.format(filename=code_path),
            )
            logger.info(f"The {i+1}th time to CodeReview: {code_path}.")
            result, rewrited_code = await self.write_code_review_and_rewrite(
                context_prompt, cr_prompt, filename=code_path
            )

            if "LBTM" in result:
                code = rewrited_code
            elif "LGTM" in result:
                break

        await awrite(filename=code_path, data=code)

        return code

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code_review_and_rewrite(self, context_prompt: str, cr_prompt: str, filename: str):
        cr_rsp = await self._aask(context_prompt + cr_prompt)
        result = CodeParser.parse_block("Code Review Result", cr_rsp)
        if "LGTM" in result:
            return result, None

        # if LBTM, rewrite code
        rewrite_prompt = f"{context_prompt}\n{cr_rsp}\n{REWRITE_CODE_TEMPLATE.format(filename=filename)}"
        code_rsp = await self._aask(rewrite_prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return result, code

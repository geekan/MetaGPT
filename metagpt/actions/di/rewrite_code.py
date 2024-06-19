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

    async def run(self, code_path: str, design_doc: str = "", task_doc: str = "", code_review_k_times: int = 2) -> str:
        """Reviews the provided code based on the accompanying design and task documentation, return the complete and correct code.

        Read the code from `code_path`, and write the final code to `code_path`.
        If there is no `design_doc` or `task_doc`, it will return and do nothing.

        Args:
            code_path (str): The file path of the code snippet to be reviewed. This should be a string containing the path to the source code file.
            design_doc (str): The design document associated with the code. This should describe the system architecture, used in the code. It helps provide context for the review process.
            task_doc (str): The task document describing what the code is intended to accomplish. This should outline the functional requirements or objectives of the code.
            code_review_k_times (int, optional): The number of iterations for reviewing and potentially rewriting the code. Defaults to 2.

        Returns:
            str: The potentially corrected or approved code after review.

        Example Usage:
            # Example of how to call the run method with a code snippet and documentation
            await WriteCodeReview().run(
                code_path="/tmp/game.js",
                design_doc='{"Implementation approach":"We will implement the 2048 game..."}',
                task_doc='{"Required packages":["No third-party dependencies required"],"..."}'
            )
        """
        if not design_doc or not task_doc:
            return

        code = await aread(code_path)

        context = "\n".join(
            [
                "## System Design\n" + design_doc + "\n",
                "## Task\n" + task_doc + "\n",
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

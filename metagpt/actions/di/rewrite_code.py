import asyncio
import os
from pathlib import Path

from metagpt.actions.action import Action
from metagpt.actions.write_code_review import (
    EXAMPLE_AND_INSTRUCTION,
    FORMAT_EXAMPLE,
    PROMPT_TEMPLATE,
    WriteCodeReview,
)
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import aread, awrite


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
            await RewriteCode().run(
                code_path="/tmp/game.js",
                design_doc_input="/tmp/design_doc.json",
                task_doc_input='{"Required packages":["No third-party dependencies required"], ...}'
            )
        """

        if not design_doc_input or not task_doc_input:
            return

        code, design_doc, task_doc = await asyncio.gather(
            aread(code_path), self._try_aread(design_doc_input), self._try_aread(task_doc_input)
        )
        code_doc = self._create_code_doc(code_path=code_path, code=code)
        reviewer = WriteCodeReview(i_context=CodingContext(filename=code_doc.filename))

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
            result, rewrited_code = await reviewer.write_code_review_and_rewrite(
                context_prompt, cr_prompt, doc=code_doc
            )

            if "LBTM" in result:
                code = rewrited_code
            elif "LGTM" in result:
                break

        await awrite(filename=code_path, data=code)

        return code

    @staticmethod
    async def _try_aread(input: str) -> str:
        """Try to read from the path if it's a file; return input directly if not."""

        if os.path.exists(input):
            return await aread(input)

        return input

    @staticmethod
    def _create_code_doc(code_path: str, code: str) -> Document:
        """Create a Document to represent the code doc."""

        path = Path(code_path)

        return Document(root_path=str(path.parent), filename=path.name, content=code)

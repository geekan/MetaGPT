from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action import Action
from metagpt.actions.write_code_review import (
    EXAMPLE_AND_INSTRUCTION,
    FORMAT_EXAMPLE,
    PROMPT_TEMPLATE,
    REWRITE_CODE_TEMPLATE,
)
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, aread, awrite


@register_tool(tags=["RewriteCode"], include_functions=["run"])
class RewriteCode(Action):
    """Accordding design doc and task doc to review the code, to make the complete and correct code."""

    name: str = "RewriteCode"

    async def run(self, code_path: str, design_doc: str = "", task_doc: str = "", code_review_k_times: int = 2) -> str:
        """Reviews the provided code based on the accompanying design and task documentation, return the complete and correct code.

        Read the code from `code_path`, and write the final code to `code_path`.

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
                design_doc='{"Implementation approach":"We will implement the 2048 game using plain JavaScript and HTML, ensuring no frameworks are used. The game logic will handle tile movements, merging, and game state updates. The UI will be simple and clean, with a responsive design to fit different screen sizes. We will use CSS for styling and ensure the game is playable with keyboard arrow keys. The game will display the current score, have a restart button, and show a game over message when no more moves are possible.","File list":["index.html","style.css","script.js"],"Data structures and interfaces":"\nclassDiagram\n    class Game {\n        -grid: int[][]\n        -score: int\n        +init(): void\n        +move(direction: str): void\n        +merge(direction: str): void\n        +isGameOver(): bool\n        +restart(): void\n    }\n    class UI {\n        -game: Game\n        +init(): void\n        +update(): void\n        +showGameOver(): void\n        +bindEvents(): void\n    }\n    Game --> UI\n","Program call flow":"\nsequenceDiagram\n    participant U as UI\n    participant G as Game\n    U->>G: init()\n    G-->>U: return\n    U->>U: bindEvents()\n    U->>G: move(direction)\n    G->>G: merge(direction)\n    G->>U: update()\n    U->>U: update()\n    U->>G: isGameOver()\n    G-->>U: return bool\n    alt Game Over\n        U->>U: showGameOver()\n    end\n    U->>G: restart()\n    G-->>U: return\n","Anything UNCLEAR":"Clarify if there are any specific design preferences or additional features required beyond the basic 2048 game functionality."}',
                task_doc='{"Required packages":["No third-party dependencies required"],"Required Other language third-party packages":["No third-party dependencies required"],"Logic Analysis":[["script.js","Contains Game and UI classes, and their methods: init, move, merge, isGameOver, restart, update, showGameOver, bindEvents"],["index.html","Contains the HTML structure for the game UI"],["style.css","Contains the CSS styles for the game UI"]],"Task list":["index.html","style.css","script.js"],"Full API spec":"","Shared Knowledge":"The `script.js` file will contain the core game logic and UI handling. The `index.html` file will provide the structure for the game, and `style.css` will handle the styling.","Anything UNCLEAR":"Clarify if there are any specific design preferences or additional features required beyond the basic 2048 game functionality."}'
            )
        """
        code = await aread(code_path)

        context = "\n".join(
            [
                "## System Design\n" + design_doc + "\n",
                "## Task\n" + task_doc + "\n",
            ]
        )

        for _ in range(code_review_k_times):
            context_prompt = PROMPT_TEMPLATE.format(context=context, code=code, filename=code_path)
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=FORMAT_EXAMPLE.format(filename=code_path),
            )
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

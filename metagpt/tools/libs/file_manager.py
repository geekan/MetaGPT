import os
import shutil
import subprocess

from pydantic import BaseModel, Field

from metagpt.tools.tool_registry import register_tool


class FileBlock(BaseModel):
    """A block of content in a file"""

    file_path: str
    block_content: str
    block_start_line: int
    block_end_line: int
    symbol: str = Field(default="", description="The symbol of interest in the block, empty if not applicable.")
    symbol_line: int = Field(default=-1, description="The line number of the symbol in the file, -1 if not applicable")


@register_tool()
class FileManager:
    """A tool for reading, understanding, writing, and editing files"""

    def write(self, path: str, content: str):
        """Write the whole content to a file."""
        with open(path, "w") as f:
            f.write(content)

    def read(self, path: str) -> str:
        """Read the whole content of a file."""
        with open(path, "r") as f:
            return f.read()

    def search_content(self, symbol: str, root_path: str = "", window: int = 20) -> FileBlock:
        """
        Search symbol in all files under root_path, return the context of symbol with window size
        Useful for locating class or function in a large codebase. Example symbol can be "def some_function", "class SomeClass", etc.

        Args:
            symbol (str): The symbol to search.
            root_path (str, optional): The root path to search in. If not provided, search in the current directory. Defaults to "".
            window (int, optional): The window size to return. Defaults to 20.

        Returns:
            FileBlock: The block containing the symbol, a pydantic BaseModel with the schema below.
            class FileBlock(BaseModel):
                file_path: str
                block_content: str
                block_start_line: int
                block_end_line: int
                symbol: str = Field(default="", description="The symbol of interest in the block, empty if not applicable.")
                symbol_line: int = Field(default=-1, description="The line number of the symbol in the file, -1 if not applicable")
        """
        for root, _, files in os.walk(root_path or "."):
            for file in files:
                file_path = os.path.join(root, file)
                if not file.endswith(".py"):
                    continue
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        lines = f.readlines()
                    except Exception:
                        continue
                for i, line in enumerate(lines):
                    if symbol in line:
                        start = max(i - window, 0)
                        end = min(i + window, len(lines) - 1)
                        block_content = "".join(lines[start : end + 1])
                        return FileBlock(
                            file_path=file_path,
                            block_content=block_content,
                            block_start_line=start + 1,
                            block_end_line=end + 1,
                            symbol=symbol,
                            symbol_line=i + 1,
                        )
        return None

    def write_content(self, file_path: str, start_line: int, end_line: int, new_block_content: str = "") -> str:
        """
        Write a new block of content into a file. Use this method to update a block of code in a file. There are three cases:
        1. If the new block content is empty, the original block will be deleted.
        2. If the new block content is not empty and end_line < start_line (e.g. set end_line = -1) the new block content will be inserted at start_line.
        3. If the new block content is not empty and end_line >= start_line, the original block from start_line to end_line (both inclusively) will be replaced by the new block content.
        This function can sometimes be used given a FileBlock upstream. Think carefully if you want to use block_start_line or symbol_line in the FileBlock as your start_line input.

        Args:
            file_path (str): The file path to write the new block content.
            start_line (int): start line of the original block to be updated.
            end_line (int): end line of the original block to be updated.
            new_block_content (str): The new block content to write.

        Returns:
            str: A message indicating the status of the write operation.
        """
        # Create a temporary copy of the file
        temp_file_path = file_path + ".temp"
        shutil.copy(file_path, temp_file_path)

        try:
            # Modify the temporary file with the new content
            self._write_content(temp_file_path, start_line, end_line, new_block_content)

            # Lint the modified temporary file
            lint_passed, lint_message = self._lint_file(temp_file_path)
            if not lint_passed:
                return f"Linting the content at a temp file, failed with:\n{lint_message}"

            # If linting passes, overwrite the original file with the temporary file
            shutil.move(temp_file_path, file_path)
            return f"Content written successfully to {file_path}"

        finally:
            # Clean up: Ensure the temporary file is removed if it still exists
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _write_content(self, file_path: str, start_line: int, end_line: int, new_block_content: str = ""):
        with open(file_path, "r") as file:
            lines = file.readlines()

        start_line_index = start_line - 1  # Adjusting because list indices start at 0
        end_line_index = end_line

        if new_block_content:
            # Split the new_block_content by newline and ensure each line ends with a newline character
            new_content_lines = [line + "\n" for line in new_block_content.split("\n")]
            if end_line >= start_line:
                # This replaces the block between start_line and end_line with new_block_content
                # irrespective of the length difference between the original and new content.
                lines[start_line_index:end_line_index] = new_content_lines
            else:
                lines.insert(start_line_index, "\n".join(new_content_lines))
        else:
            del lines[start_line_index:end_line_index]

        with open(file_path, "w") as file:
            file.writelines(lines)

    @classmethod
    def _lint_file(cls, file_path: str) -> (bool, str):
        """Lints an entire Python file using pylint, returns True if linting passes, along with pylint's output."""
        result = subprocess.run(
            ["pylint", file_path, "--disable=all", "--enable=E"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        lint_passed = result.returncode == 0
        lint_message = result.stdout
        return lint_passed, lint_message

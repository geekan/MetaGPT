import os
import shutil
import subprocess

from pydantic import BaseModel

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.report import EditorReporter


class FileBlock(BaseModel):
    """A block of content in a file"""

    file_path: str
    block_content: str


@register_tool()
class Editor:
    """A tool for reading, understanding, writing, and editing files"""

    def __init__(self) -> None:
        print(f"Editor initialized with root path at: {DEFAULT_WORKSPACE_ROOT}")
        self.resource = EditorReporter()

    def write(self, path: str, content: str):
        """Write the whole content to a file. When used, make sure content arg contains the full content of the file."""
        if "\n" not in content and "\\n" in content:
            # A very raw rule to correct the content: If 'content' lacks actual newlines ('\n') but includes '\\n', consider
            # replacing them with '\n' to potentially correct mistaken representations of newline characters.
            content = content.replace("\\n", "\n")
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        # self.resource.report(path, "path")

    def read(self, path: str) -> FileBlock:
        """Read the whole content of a file.It is strongly advised to utilize absolute paths"""
        with open(path, "r") as f:
            self.resource.report(path, "path")
            lines = f.readlines()
        lines_with_num = [f"{i + 1:03}|{line}" for i, line in enumerate(lines)]
        result = FileBlock(
            file_path=path,
            block_content="".join(lines_with_num),
        )
        return result

    def search_content(self, symbol: str, root_path: str = ".", window: int = 50) -> FileBlock:
        """
        Search symbol in all files under root_path, return the context of symbol with window size
        Useful for locating class or function in a large codebase. Example symbol can be "def some_function", "class SomeClass", etc.
        In searching, attempt different symbols of different granualities, e.g. "def some_function", "class SomeClass", a certain line of code, etc.

        Args:
            symbol (str): The symbol to search.
            root_path (str, optional): The root path to search in, the path can be a folder or a file. If not provided, search in the current directory. Defaults to ".".
            window (int, optional): The window size to return. Defaults to 20.

        Returns:
            FileBlock: The block containing the symbol, a pydantic BaseModel with the schema below.
            class FileBlock(BaseModel):
                file_path: str
                block_content: str
        """
        if not os.path.exists(root_path):
            print(f"Currently at {os.getcwd()} containing: {os.listdir()}. Path {root_path} does not exist.")
            return None
        not_found_msg = (
            "symbol not found, you may try searching another one, or break down your search term to search a part of it"
        )
        if os.path.isfile(root_path):
            result = self._search_content_in_file(symbol, root_path, window)
            if not result:
                print(not_found_msg)
            return result
        for root, _, files in os.walk(root_path or "."):
            for file in files:
                file_path = os.path.join(root, file)
                result = self._search_content_in_file(symbol, file_path, window)
                if result:
                    # FIXME: This returns the first found result, not all results.
                    return result
        print(not_found_msg)
        return None

    def _search_content_in_file(self, symbol: str, file_path: str, window: int = 50) -> FileBlock:
        print("search in", file_path)
        if not file_path.endswith(".py"):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                lines = f.readlines()
            except Exception:
                return None
        for i, line in enumerate(lines):
            if symbol in line:
                start = max(i - window, 0)
                end = min(i + window, len(lines) - 1)
                for row_num in range(start, end + 1):
                    lines[row_num] = f"{(row_num + 1):03}|{lines[row_num]}"
                block_content = "".join(lines[start : end + 1])
                result = FileBlock(
                    file_path=file_path,
                    block_content=block_content,
                )
                self.resource.report(result.file_path, "path", extra={"type": "search", "line": i, "symbol": symbol})
                return result
        return None

    def write_content(self, file_path: str, start_line: int, end_line: int, new_block_content: str = "") -> str:
        """
        Write a new block of content into a file. Use this method to update a block of code in a file. There are three cases:
        1. If the new block content is empty, the original block will be deleted.
        2. If the new block content is not empty and end_line < start_line (e.g. set end_line = -1) the new block content will be inserted at start_line.
        3. If the new block content is not empty and end_line >= start_line, the original block from start_line to end_line (both inclusively) will be replaced by the new block content.
        This function can sometimes be used given a FileBlock upstream. You should carefully review its row number. Determine the start_line and end_line based on the row number of the FileBlock.
        The file content from start_line to end_line will be replaced by your new_block_content. DON'T replace more than you intend to.

        Args:
            file_path (str): The file path to write the new block content.
            start_line (int): start line of the original block to be updated (inclusive).
            end_line (int): end line of the original block to be updated (inclusive).
            new_block_content (str): The new block content to write. Don't include row number in the content.

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
            # if not lint_passed:
            #     return f"Linting the content at a temp file, failed with:\n{lint_message}"

            # If linting passes, overwrite the original file with the temporary file
            shutil.move(temp_file_path, file_path)

            new_file_block = FileBlock(
                file_path=file_path,
                block_content=new_block_content,
            )
            self.resource.report(new_file_block.file_path, "path")

            return f"Content written successfully to {file_path}"

        finally:
            # Clean up: Ensure the temporary file is removed if it still exists
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _write_content(self, file_path: str, start_line: int, end_line: int, new_block_content: str = ""):
        """start_line and end_line are both 1-based indices and inclusive."""
        with open(file_path, "r") as file:
            lines = file.readlines()

        start_line_index = start_line - 1  # Adjusting because list indices start at 0
        end_line_index = end_line

        if new_block_content:
            # Split the new_block_content by newline and ensure each line ends with a newline character
            new_content_lines = new_block_content.splitlines(
                keepends=True
            )  # FIXME: This will split \n within a line, such as ab\ncd
            if end_line >= start_line:
                # This replaces the block between start_line and end_line with new_block_content
                # irrespective of the length difference between the original and new content.
                lines[start_line_index:end_line_index] = new_content_lines
            else:
                lines.insert(start_line_index, "".join(new_content_lines))
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

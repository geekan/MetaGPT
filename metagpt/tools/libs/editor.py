"""
This file is borrowed from OpenDevin
You can find the original repository here:
https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/plugins/agent_skills/file_ops/file_ops.py
"""
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

import tiktoken
from pydantic import BaseModel, ConfigDict

from metagpt.const import DEFAULT_MIN_TOKEN_COUNT, DEFAULT_WORKSPACE_ROOT
from metagpt.tools.libs.linter import Linter
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import awrite
from metagpt.utils.file import File
from metagpt.utils.report import EditorReporter

# This is also used in unit tests!
LINTER_ERROR_MSG = "[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]\n"


INDENTATION_INFO = """
The previous line is:
"{pre_line}"
The indentation has {pre_line_indent} spaces.

The error line is:
"{insert_line}"
The indentation has {insert_line_indent} spaces.

Please check the indentation of the code to ensure that it is not causing any errors.
Try using indentation with either {sub_4_space} or {add_4_space} spaces.
"""

ERROR_GUIDANCE = """
{linter_error_msg}

[This is how your edit would have looked if applied]
-------------------------------------------------
{window_after_applied}
-------------------------------------------------

[This is the original code before your edit]
-------------------------------------------------
{window_before_applied}
-------------------------------------------------

Your changes have NOT been applied. Please fix your edit command and try again
{guidance_message}

"""

LINE_NUMBER_AND_CONTENT_MISMATCH = """Error: The `{position}_replaced_line_number` does not match the `{position}_replaced_line_content`. Please correct the parameters.
The `{position}_replaced_line_number` is {line_number} and the corresponding content is "{true_content}".
But the `{position}_replaced_line_content ` is "{fake_content}".
The content around the specified line is:
{context}
Pay attention to the new content. Ensure that it aligns with the new parameters.
"""
SUCCESS_EDIT_INFO = """
[File: {file_name} ({n_total_lines} lines total after edit)]
{window_after_applied}
[File updated (edited at line {line_number})].
"""
# Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.


class FileBlock(BaseModel):
    """A block of content in a file"""

    file_path: str
    block_content: str


class LineNumberError(Exception):
    pass


@register_tool(
    include_functions=[
        "write",
        "read",
        "open_file",
        "goto_line",
        "scroll_down",
        "scroll_up",
        "create_file",
        "edit_file_by_replace",
        "insert_content_at_line",
        "append_file",
        "search_dir",
        "search_file",
        "find_file",
        "similarity_search",
    ]
)
class Editor(BaseModel):
    """
    A tool for reading, understanding, writing, and editing files.
    Support local file including text-based files (txt, md, json, py, html, js, css, etc.), pdf, docx, excluding images, csv, excel, or online links
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource: EditorReporter = EditorReporter()
    current_file: Optional[Path] = None
    current_line: int = 1
    window: int = 200
    enable_auto_lint: bool = False
    working_dir: Path = DEFAULT_WORKSPACE_ROOT

    def write(self, path: str, content: str):
        """Write the whole content to a file. When used, make sure content arg contains the full content of the file."""

        path = self._try_fix_path(path)

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
        return f"The writing/coding the of the file {os.path.basename(path)}' is now completed. The file '{os.path.basename(path)}' has been successfully created."

    async def read(self, path: str) -> FileBlock:
        """Read the whole content of a file. Using absolute paths as the argument for specifying the file location."""

        path = self._try_fix_path(path)

        error = FileBlock(
            file_path=str(path),
            block_content="The file is too large to read. Use `Editor.similarity_search` to read the file instead.",
        )
        path = Path(path)
        if path.stat().st_size > 5 * DEFAULT_MIN_TOKEN_COUNT:
            return error
        content = await File.read_text_file(path)
        if not content:
            return FileBlock(file_path=str(path), block_content="")
        if self.is_large_file(content=content):
            return error
        self.resource.report(str(path), "path")

        lines = content.splitlines(keepends=True)
        lines_with_num = [f"{i + 1:03}|{line}" for i, line in enumerate(lines)]
        result = FileBlock(
            file_path=str(path),
            block_content="".join(lines_with_num),
        )
        return result

    @staticmethod
    def _is_valid_filename(file_name: str) -> bool:
        if not file_name or not file_name.strip():
            return False
        invalid_chars = '<>:"/\\|?*'
        if os.name == "nt":  # Windows
            invalid_chars = '<>:"/\\|?*'
        elif os.name == "posix":  # Unix-like systems
            invalid_chars = "\0"

        for char in invalid_chars:
            if char in file_name:
                return False
        return True

    @staticmethod
    def _is_valid_path(path: Path) -> bool:
        try:
            return path.exists()
        except PermissionError:
            return False

    @staticmethod
    def _create_paths(file_path: Path) -> bool:
        try:
            if file_path.parent:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            return False

    def _check_current_file(self, file_path: Optional[Path] = None) -> bool:
        if file_path is None:
            file_path = self.current_file
        if not file_path or not file_path.is_file():
            raise ValueError("No file open. Use the open_file function first.")
        return True

    @staticmethod
    def _clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))

    def _lint_file(self, file_path: Path) -> tuple[Optional[str], Optional[int]]:
        """Lint the file at the given path and return a tuple with a boolean indicating if there are errors,
        and the line number of the first error, if any.

        Returns:
            tuple[str | None, int | None]: (lint_error, first_error_line_number)
        """

        linter = Linter(root=self.working_dir)
        lint_error = linter.lint(str(file_path))
        if not lint_error:
            # Linting successful. No issues found.
            return None, None
        return "ERRORS:\n" + lint_error.text, lint_error.lines[0]

    def _print_window(self, file_path: Path, targeted_line: int, window: int):
        self._check_current_file(file_path)
        with file_path.open() as file:
            content = file.read()

            # Ensure the content ends with a newline character
            if not content.endswith("\n"):
                content += "\n"

            lines = content.splitlines(True)  # Keep all line ending characters
            total_lines = len(lines)

            # cover edge cases
            self.current_line = self._clamp(targeted_line, 1, total_lines)
            half_window = max(1, window // 2)

            # Ensure at least one line above and below the targeted line
            start = max(1, self.current_line - half_window)
            end = min(total_lines, self.current_line + half_window)

            # Adjust start and end to ensure at least one line above and below
            if start == 1:
                end = min(total_lines, start + window - 1)
            if end == total_lines:
                start = max(1, end - window + 1)

            output = ""

            # only display this when there's at least one line above
            if start > 1:
                output += f"({start - 1} more lines above)\n"
            else:
                output += "(this is the beginning of the file)\n"
            for i in range(start, end + 1):
                _new_line = f"{i:03d}|{lines[i - 1]}"
                if not _new_line.endswith("\n"):
                    _new_line += "\n"
                output += _new_line
            if end < total_lines:
                output += f"({total_lines - end} more lines below)\n"
            else:
                output += "(this is the end of the file)\n"
            output = output.rstrip()

            return output

    @staticmethod
    def _cur_file_header(current_file: Path, total_lines: int) -> str:
        if not current_file:
            return ""
        return f"[File: {current_file.resolve()} ({total_lines} lines total)]\n"

    def _set_workdir(self, path: str) -> None:
        """
        Sets the working directory to the given path. eg: repo directory.
        You MUST to set it up before open the file.

        Args:
            path: str: The path to set as the working directory.
        """
        self.working_dir = Path(path)

    def open_file(
        self, path: Union[Path, str], line_number: Optional[int] = 1, context_lines: Optional[int] = None
    ) -> str:
        """Opens the file at the given path in the editor. If line_number is provided, the window will be moved to include that line.
        It only shows the first 100 lines by default! Max `context_lines` supported is 2000, use `scroll up/down`
        to view the file if you want to see more.

        Args:
            path: str: The path to the file to open, preferred absolute path.
            line_number: int | None = 1: The line number to move to. Defaults to 1.
            context_lines: int | None = 100: Only shows this number of lines in the context window (usually from line 1), with line_number as the center (if possible). Defaults to 100.
        """
        if context_lines is None:
            context_lines = self.window

        path = self._try_fix_path(path)

        if not path.is_file():
            raise FileNotFoundError(f"File {path} not found")

        self.current_file = path
        with path.open() as file:
            total_lines = max(1, sum(1 for _ in file))

        if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
            raise ValueError(f"Line number must be between 1 and {total_lines}")
        self.current_line = line_number

        # Override WINDOW with context_lines
        if context_lines is None or context_lines < 1:
            context_lines = self.window

        output = self._cur_file_header(path, total_lines)
        output += self._print_window(path, self.current_line, self._clamp(context_lines, 1, 2000))
        self.resource.report(path, "path")
        return output

    def goto_line(self, line_number: int) -> str:
        """Moves the window to show the specified line number.

        Args:
            line_number: int: The line number to move to.
        """
        self._check_current_file()

        with self.current_file.open() as file:
            total_lines = max(1, sum(1 for _ in file))
        if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
            raise ValueError(f"Line number must be between 1 and {total_lines}")

        self.current_line = self._clamp(line_number, 1, total_lines)

        output = self._cur_file_header(self.current_file, total_lines)
        output += self._print_window(self.current_file, self.current_line, self.window)
        return output

    def scroll_down(self) -> str:
        """Moves the window down by 100 lines."""
        self._check_current_file()

        with self.current_file.open() as file:
            total_lines = max(1, sum(1 for _ in file))
        self.current_line = self._clamp(self.current_line + self.window, 1, total_lines)
        output = self._cur_file_header(self.current_file, total_lines)
        output += self._print_window(self.current_file, self.current_line, self.window)
        return output

    def scroll_up(self) -> str:
        """Moves the window up by 100 lines."""
        self._check_current_file()

        with self.current_file.open() as file:
            total_lines = max(1, sum(1 for _ in file))
        self.current_line = self._clamp(self.current_line - self.window, 1, total_lines)
        output = self._cur_file_header(self.current_file, total_lines)
        output += self._print_window(self.current_file, self.current_line, self.window)
        return output

    async def create_file(self, filename: str) -> str:
        """Creates and opens a new file with the given name.

        Args:
            filename: str: The name of the file to create. If the parent directory does not exist, it will be created.
        """
        filename = self._try_fix_path(filename)

        if filename.exists():
            raise FileExistsError(f"File '{filename}' already exists.")
        await awrite(filename, "\n")

        self.open_file(filename)
        return f"[File {filename} created.]"

    @staticmethod
    def _append_impl(lines, content):
        """Internal method to handle appending to a file.

        Args:
            lines: list[str]: The lines in the original file.
            content: str: The content to append to the file.

        Returns:
            content: str: The new content of the file.
            n_added_lines: int: The number of lines added to the file.
        """
        content_lines = content.splitlines(keepends=True)
        n_added_lines = len(content_lines)
        if lines and not (len(lines) == 1 and lines[0].strip() == ""):
            # file is not empty
            if not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            new_lines = lines + content_lines
            content = "".join(new_lines)
        else:
            # file is empty
            content = "".join(content_lines)

        return content, n_added_lines

    @staticmethod
    def _insert_impl(lines, start, content):
        """Internal method to handle inserting to a file.

        Args:
            lines: list[str]: The lines in the original file.
            start: int: The start line number for inserting.
            content: str: The content to insert to the file.

        Returns:
            content: str: The new content of the file.
            n_added_lines: int: The number of lines added to the file.

        Raises:
            LineNumberError: If the start line number is invalid.
        """
        inserted_lines = [content + "\n" if not content.endswith("\n") else content]
        if len(lines) == 0:
            new_lines = inserted_lines
        elif start is not None:
            if len(lines) == 1 and lines[0].strip() == "":
                # if the file with only 1 line and that line is empty
                lines = []

            if len(lines) == 0:
                new_lines = inserted_lines
            else:
                new_lines = lines[: start - 1] + inserted_lines + lines[start - 1 :]
        else:
            raise LineNumberError(
                f"Invalid line number: {start}. Line numbers must be between 1 and {len(lines)} (inclusive)."
            )

        content = "".join(new_lines)
        n_added_lines = len(inserted_lines)
        return content, n_added_lines

    @staticmethod
    def _edit_impl(lines, start, end, content):
        """Internal method to handle editing a file.

        REQUIRES (should be checked by caller):
            start <= end
            start and end are between 1 and len(lines) (inclusive)
            content ends with a newline

        Args:
            lines: list[str]: The lines in the original file.
            start: int: The start line number for editing.
            end: int: The end line number for editing.
            content: str: The content to replace the lines with.

        Returns:
            content: str: The new content of the file.
            n_added_lines: int: The number of lines added to the file.
        """
        # Handle cases where start or end are None
        if start is None:
            start = 1  # Default to the beginning
        if end is None:
            end = len(lines)  # Default to the end
        # Check arguments
        if not (1 <= start <= len(lines)):
            raise LineNumberError(
                f"Invalid start line number: {start}. Line numbers must be between 1 and {len(lines)} (inclusive)."
            )
        if not (1 <= end <= len(lines)):
            raise LineNumberError(
                f"Invalid end line number: {end}. Line numbers must be between 1 and {len(lines)} (inclusive)."
            )
        if start > end:
            raise LineNumberError(f"Invalid line range: {start}-{end}. Start must be less than or equal to end.")

        # Split content into lines and ensure it ends with a newline
        if not content.endswith("\n"):
            content += "\n"
        content_lines = content.splitlines(True)

        # Calculate the number of lines to be added
        n_added_lines = len(content_lines)

        # Remove the specified range of lines and insert the new content
        new_lines = lines[: start - 1] + content_lines + lines[end:]

        # Handle the case where the original lines are empty
        if len(lines) == 0:
            new_lines = content_lines

        # Join the lines to create the new content
        content = "".join(new_lines)
        return content, n_added_lines

    def _get_indentation_info(self, content, first_line):
        """
        The indentation of the first insert line and the previous line, along with guidance for the next attempt.
        """
        content_lines = content.split("\n")
        pre_line = content_lines[first_line - 2] if first_line - 2 >= 0 else ""
        pre_line_indent = len(pre_line) - len(pre_line.lstrip())
        insert_line = content_lines[first_line - 1]
        insert_line_indent = len(insert_line) - len(insert_line.lstrip())
        ret_str = INDENTATION_INFO.format(
            pre_line=pre_line,
            pre_line_indent=pre_line_indent,
            insert_line=insert_line,
            insert_line_indent=insert_line_indent,
            sub_4_space=max(insert_line_indent - 4, 0),
            add_4_space=insert_line_indent + 4,
        )
        return ret_str

    def _edit_file_impl(
        self,
        file_name: Path,
        start: Optional[int] = None,
        end: Optional[int] = None,
        content: str = "",
        is_insert: bool = False,
        is_append: bool = False,
    ) -> str:
        """Internal method to handle common logic for edit_/append_file methods.

        Args:
            file_name: Path: The name of the file to edit or append to.
            start: int | None = None: The start line number for editing. Ignored if is_append is True.
            end: int | None = None: The end line number for editing. Ignored if is_append is True.
            content: str: The content to replace the lines with or to append.
            is_insert: bool = False: Whether to insert content at the given line number instead of editing.
            is_append: bool = False: Whether to append content to the file instead of editing.
        """

        ERROR_MSG = f"[Error editing file {file_name}. Please confirm the file is correct.]"
        ERROR_MSG_SUFFIX = (
            "Your changes have NOT been applied. Please fix your edit command and try again.\n"
            "You either need to 1) Open the correct file and try again or 2) Specify the correct line number arguments.\n"
            "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
        )

        if not self._is_valid_filename(file_name.name):
            raise FileNotFoundError("Invalid file name.")

        if not self._is_valid_path(file_name):
            raise FileNotFoundError("Invalid path or file name.")

        if not self._create_paths(file_name):
            raise PermissionError("Could not access or create directories.")

        if not file_name.is_file():
            raise FileNotFoundError(f"File {file_name} not found.")

        if is_insert and is_append:
            raise ValueError("Cannot insert and append at the same time.")

        # Use a temporary file to write changes
        content = str(content or "")
        temp_file_path = ""
        src_abs_path = file_name.resolve()
        first_error_line = None
        # The file to store previous content and will be removed automatically.
        temp_backup_file = tempfile.NamedTemporaryFile("w", delete=True)

        try:
            # lint the original file
            # enable_auto_lint = os.getenv("ENABLE_AUTO_LINT", "false").lower() == "true"
            if self.enable_auto_lint:
                original_lint_error, _ = self._lint_file(file_name)

            # Create a temporary file
            with tempfile.NamedTemporaryFile("w", delete=False) as temp_file:
                temp_file_path = temp_file.name

                # Read the original file and check if empty and for a trailing newline
                with file_name.open() as original_file:
                    lines = original_file.readlines()

                if is_append:
                    content, n_added_lines = self._append_impl(lines, content)
                elif is_insert:
                    try:
                        content, n_added_lines = self._insert_impl(lines, start, content)
                    except LineNumberError as e:
                        return (f"{ERROR_MSG}\n" f"{e}\n" f"{ERROR_MSG_SUFFIX}") + "\n"
                else:
                    try:
                        content, n_added_lines = self._edit_impl(lines, start, end, content)
                    except LineNumberError as e:
                        return (f"{ERROR_MSG}\n" f"{e}\n" f"{ERROR_MSG_SUFFIX}") + "\n"

                if not content.endswith("\n"):
                    content += "\n"

                # Write the new content to the temporary file
                temp_file.write(content)

            # Replace the original file with the temporary file atomically
            shutil.move(temp_file_path, src_abs_path)

            # Handle linting
            # NOTE: we need to get env var inside this function
            # because the env var will be set AFTER the agentskills is imported
            if self.enable_auto_lint:
                # BACKUP the original file
                temp_backup_file.writelines(lines)
                temp_backup_file.flush()
                lint_error, first_error_line = self._lint_file(file_name)

                # Select the errors caused by the modification
                def extract_last_part(line):
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[-1].strip()
                    return line.strip()

                def subtract_strings(str1, str2) -> str:
                    lines1 = str1.splitlines()
                    lines2 = str2.splitlines()

                    last_parts1 = [extract_last_part(line) for line in lines1]

                    remaining_lines = [line for line in lines2 if extract_last_part(line) not in last_parts1]

                    result = "\n".join(remaining_lines)
                    return result

                if original_lint_error and lint_error:
                    lint_error = subtract_strings(original_lint_error, lint_error)
                    if lint_error == "":
                        lint_error = None
                        first_error_line = None

                if lint_error is not None:
                    # if first_error_line is not None:
                    #     show_line = int(first_error_line)

                    # show the first insert line.
                    if is_append:
                        # original end-of-file
                        show_line = len(lines)
                    # insert OR edit WILL provide meaningful line numbers
                    elif start is not None and end is not None:
                        show_line = int((start + end) / 2)
                    else:
                        raise ValueError("Invalid state. This should never happen.")

                    guidance_message = self._get_indentation_info(content, start or len(lines))
                    guidance_message += (
                        "You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.\n"
                        "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
                    )
                    lint_error_info = ERROR_GUIDANCE.format(
                        linter_error_msg=LINTER_ERROR_MSG + lint_error,
                        window_after_applied=self._print_window(file_name, show_line, n_added_lines + 20),
                        window_before_applied=self._print_window(
                            Path(temp_backup_file.name), show_line, n_added_lines + 20
                        ),
                        guidance_message=guidance_message,
                    ).strip()

                    # recover the original file
                    shutil.move(temp_backup_file.name, src_abs_path)
                    return lint_error_info

        except FileNotFoundError as e:
            return f"File not found: {e}\n"
        except IOError as e:
            return f"An error occurred while handling the file: {e}\n"
        except ValueError as e:
            return f"Invalid input: {e}\n"
        except Exception as e:
            guidance_message = self._get_indentation_info(content, start or len(lines))
            guidance_message += (
                "You either need to 1) Specify the correct start/end line arguments or 2) Enlarge the range of original code.\n"
                "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
            )
            error_info = ERROR_GUIDANCE.format(
                linter_error_msg=LINTER_ERROR_MSG + str(e),
                window_after_applied=self._print_window(file_name, start or len(lines), 100),
                window_before_applied=self._print_window(Path(temp_backup_file.name), start or len(lines), 100),
                guidance_message=guidance_message,
            ).strip()
            # Clean up the temporary file if an error occurs
            shutil.move(temp_backup_file.name, src_abs_path)
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()

            # logger.warning(f"An unexpected error occurred: {e}")
            raise Exception(f"{error_info}") from e
        # Update the file information and print the updated content
        with file_name.open("r", encoding="utf-8") as file:
            n_total_lines = max(1, len(file.readlines()))
        if first_error_line is not None and int(first_error_line) > 0:
            self.current_line = first_error_line
        else:
            if is_append:
                self.current_line = max(1, len(lines))  # end of original file
            else:
                self.current_line = start or n_total_lines or 1
        success_edit_info = SUCCESS_EDIT_INFO.format(
            file_name=file_name.resolve(),
            n_total_lines=n_total_lines,
            window_after_applied=self._print_window(file_name, self.current_line, self.window),
            line_number=self.current_line,
        ).strip()
        return success_edit_info

    def edit_file_by_replace(
        self,
        file_name: str,
        first_replaced_line_number: int,
        first_replaced_line_content: str,
        last_replaced_line_number: int,
        last_replaced_line_content: str,
        new_content: str,
    ) -> str:
        """
        Line numbers start from 1. Replace lines from start_line to end_line (inclusive) with the new_content in the open file.
        All of the new_content will be entered, so makesure your indentation is formatted properly.
        The new_content must be a complete block of code.

        Example 1:
        Given a file "/workspace/example.txt" with the following content:
        ```
        001|contain f
        002|contain g
        003|contain h
        004|contain i
        ```

        EDITING: If you want to replace line 2 and line 3

        edit_file_by_replace(
            "/workspace/example.txt",
            first_replaced_line_number=2,
            first_replaced_line_content="contain g",
            last_replaced_line_number=3,
            last_replaced_line_content="contain h",
            new_content="new content",
        )
        This will replace the second line 2 and line 3 with "new content".

        The resulting file will be:
        ```
        001|contain f
        002|new content
        003|contain i
        ```
        Example 2:
        Given a file "/workspace/example.txt" with the following content:
        ```
        001|contain f
        002|contain g
        003|contain h
        004|contain i
        ```
        EDITING: If you want to remove the line 2 and line 3.
        edit_file_by_replace(
            "/workspace/example.txt",
            first_replaced_line_number=2,
            first_replaced_line_content="contain g",
            last_replaced_line_number=3,
            last_replaced_line_content="contain h",
            new_content="",
        )
        This will remove line 2 and line 3.
        The resulting file will be:
        ```
        001|contain f
        002|
        003|contain i
        ```
        Args:
            file_name (str): The name of the file to edit.
            first_replaced_line_number (int): The line number to start the edit at, starting from 1.
            first_replaced_line_content (str): The content of the start replace line, according to the first_replaced_line_number.
            last_replaced_line_number (int): The line number to end the edit at (inclusive), starting from 1.
            last_replaced_line_content (str): The content of the end replace line, according to the last_replaced_line_number.
            new_content (str): The text to replace the current selection with, must conform to PEP8 standards. The content in the start line and end line will also be replaced.

        """

        file_name = self._try_fix_path(file_name)

        # Check if the first_replaced_line_number  and last_replaced_line_number  correspond to the appropriate content.
        mismatch_error = ""
        with file_name.open() as file:
            content = file.read()
            # Ensure the content ends with a newline character
            if not content.endswith("\n"):
                content += "\n"
            lines = content.splitlines(True)
            total_lines = len(lines)
            check_list = [
                ("first", first_replaced_line_number, first_replaced_line_content),
                ("last", last_replaced_line_number, last_replaced_line_content),
            ]
            for position, line_number, line_content in check_list:
                if line_number > len(lines) or lines[line_number - 1].rstrip() != line_content:
                    start = max(1, line_number - 3)
                    end = min(total_lines, line_number + 3)
                    context = "\n".join(
                        [
                            f'The {cur_line_number:03d} line is "{lines[cur_line_number-1].rstrip()}"'
                            for cur_line_number in range(start, end + 1)
                        ]
                    )
                    mismatch_error += LINE_NUMBER_AND_CONTENT_MISMATCH.format(
                        position=position,
                        line_number=line_number,
                        true_content=lines[line_number - 1].rstrip()
                        if line_number - 1 < len(lines)
                        else "OUT OF FILE RANGE!",
                        fake_content=line_content.replace("\n", "\\n"),
                        context=context.strip(),
                    )
        if mismatch_error:
            raise ValueError(mismatch_error)
        ret_str = self._edit_file_impl(
            file_name,
            start=first_replaced_line_number,
            end=last_replaced_line_number,
            content=new_content,
        )
        # TODO: automatically tries to fix linter error (maybe involve some static analysis tools on the location near the edit to figure out indentation)
        self.resource.report(file_name, "path")
        return ret_str

    def _edit_file_by_replace(self, file_name: str, to_replace: str, new_content: str) -> str:
        """Edit a file. This will search for `to_replace` in the given file and replace it with `new_content`.

        Every *to_replace* must *EXACTLY MATCH* the existing source code, character for character, including all comments, docstrings, etc.

        Include enough lines to make code in `to_replace` unique. `to_replace` should NOT be empty.

        For example, given a file "/workspace/example.txt" with the following content:
        ```
        line 1
        line 2
        line 2
        line 3
        ```

        EDITING: If you want to replace the second occurrence of "line 2", you can make `to_replace` unique:

        edit_file_by_replace(
            '/workspace/example.txt',
            to_replace='line 2\nline 3',
            new_content='new line\nline 3',
        )

        This will replace only the second "line 2" with "new line". The first "line 2" will remain unchanged.

        The resulting file will be:
        ```
        line 1
        line 2
        new line
        line 3
        ```

        REMOVAL: If you want to remove "line 2" and "line 3", you can set `new_content` to an empty string:

        edit_file_by_replace(
            '/workspace/example.txt',
            to_replace='line 2\nline 3',
            new_content='',
        )

        Args:
            file_name: (str): The name of the file to edit.
            to_replace: (str): The content to search for and replace.
            new_content: (str): The new content to replace the old content with.
        NOTE:
            This tool is exclusive. If you use this tool, you cannot use any other commands in the current response.
            If you need to use it multiple times, wait for the next turn.
        """
        # FIXME: support replacing *all* occurrences

        if to_replace == new_content:
            raise ValueError("`to_replace` and `new_content` must be different.")

        # search for `to_replace` in the file
        # if found, replace it with `new_content`
        # if not found, perform a fuzzy search to find the closest match and replace it with `new_content`
        file_name = self._try_fix_path(file_name)
        with file_name.open("r") as file:
            file_content = file.read()

        if to_replace.strip() == "":
            if file_content.strip() == "":
                raise ValueError(f"The file '{file_name}' is empty. Please use the append method to add content.")
            raise ValueError("`to_replace` must not be empty.")

        if file_content.count(to_replace) > 1:
            raise ValueError(
                "`to_replace` appears more than once, please include enough lines to make code in `to_replace` unique."
            )
        start = file_content.find(to_replace)
        if start != -1:
            # Convert start from index to line number
            start_line_number = file_content[:start].count("\n") + 1
            end_line_number = start_line_number + len(to_replace.splitlines()) - 1
        else:

            def _fuzzy_transform(s: str) -> str:
                # remove all space except newline
                return re.sub(r"[^\S\n]+", "", s)

            # perform a fuzzy search (remove all spaces except newlines)
            to_replace_fuzzy = _fuzzy_transform(to_replace)
            file_content_fuzzy = _fuzzy_transform(file_content)
            # find the closest match
            start = file_content_fuzzy.find(to_replace_fuzzy)
            if start == -1:
                return f"[No exact match found in {file_name} for\n```\n{to_replace}\n```\n]"
            # Convert start from index to line number for fuzzy match
            start_line_number = file_content_fuzzy[:start].count("\n") + 1
            end_line_number = start_line_number + len(to_replace.splitlines()) - 1

        ret_str = self._edit_file_impl(
            file_name,
            start=start_line_number,
            end=end_line_number,
            content=new_content,
            is_insert=False,
        )
        # lint_error = bool(LINTER_ERROR_MSG in ret_str)
        # TODO: automatically tries to fix linter error (maybe involve some static analysis tools on the location near the edit to figure out indentation)
        self.resource.report(file_name, "path")
        return ret_str

    def insert_content_at_line(self, file_name: str, line_number: int, insert_content: str) -> str:
        """Insert a complete block of code before the given line number in a file. That is, the new content will start at the beginning of the specified line, and the existing content of that line will be moved down.
        This operation will NOT modify the content of the lines before or after the given line number.
        This function can not insert content the end of the file. Please use append_file instead,
        For example, if the file has the following content:
        ```
        001|contain g
        002|contain h
        003|contain i
        004|contain j
        ```
        and you call
        insert_content_at_line(
            file_name='file.txt',
            line_number=2,
            insert_content='new line'
        )
        the file will be updated to:
        ```
        001|contain g
        002|new line
        003|contain h
        004|contain i
        005|contain j
        ```

        Args:
            file_name: (str): The name of the file to edit.
            line_number (int): The line number (starting from 1) to insert the content after. The insert content will be add between the line of line_number-1 and line_number
            insert_content (str): The content to insert betweed the previous_line_content and current_line_content.The insert_content must be a complete block of code at.

        NOTE:
            This tool is exclusive. If you use this tool, you cannot use any other commands in the current response.
            If you need to use it multiple times, wait for the next turn.
        """
        file_name = self._try_fix_path(file_name)
        ret_str = self._edit_file_impl(
            file_name,
            start=line_number,
            end=line_number,
            content=insert_content,
            is_insert=True,
            is_append=False,
        )
        self.resource.report(file_name, "path")
        return ret_str

    def append_file(self, file_name: str, content: str) -> str:
        """Append content to the given file.
        It appends text `content` to the end of the specified file.

        Args:
            file_name: str: The name of the file to edit.
            content: str: The content to insert.
        NOTE:
            This tool is exclusive. If you use this tool, you cannot use any other commands in the current response.
            If you need to use it multiple times, wait for the next turn.
        """
        file_name = self._try_fix_path(file_name)
        ret_str = self._edit_file_impl(
            file_name,
            start=None,
            end=None,
            content=content,
            is_insert=False,
            is_append=True,
        )
        self.resource.report(file_name, "path")
        return ret_str

    def search_dir(self, search_term: str, dir_path: str = "./") -> str:
        """Searches for search_term in all files in dir. If dir is not provided, searches in the current directory.

        Args:
            search_term: str: The term to search for.
            dir_path: str: The path to the directory to search.
        """
        dir_path = self._try_fix_path(dir_path)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Directory {dir_path} not found")
        matches = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.startswith("."):
                    continue
                file_path = Path(root) / file
                with file_path.open("r", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if search_term in line:
                            matches.append((file_path, line_num, line.strip()))

        if not matches:
            return f'No matches found for "{search_term}" in {dir_path}'

        num_matches = len(matches)
        num_files = len(set(match[0] for match in matches))

        if num_files > 100:
            return f'More than {num_files} files matched for "{search_term}" in {dir_path}. Please narrow your search.'

        res_list = [f'[Found {num_matches} matches for "{search_term}" in {dir_path}]']
        for file_path, line_num, line in matches:
            res_list.append(f"{file_path} (Line {line_num}): {line}")
        res_list.append(f'[End of matches for "{search_term}" in {dir_path}]')
        return "\n".join(res_list)

    def search_file(self, search_term: str, file_path: Optional[str] = None) -> str:
        """Searches for search_term in file. If file is not provided, searches in the current open file.

        Args:
            search_term: str: The term to search for.
            file_path: str | None: The path to the file to search.
        """
        if file_path is None:
            file_path = self.current_file
        else:
            file_path = self._try_fix_path(file_path)
        if file_path is None:
            raise FileNotFoundError("No file specified or open. Use the open_file function first.")
        if not file_path.is_file():
            raise FileNotFoundError(f"File {file_path} not found")

        matches = []
        with file_path.open() as file:
            for i, line in enumerate(file, 1):
                if search_term in line:
                    matches.append((i, line.strip()))
        res_list = []
        if matches:
            res_list.append(f'[Found {len(matches)} matches for "{search_term}" in {file_path}]')
            for match in matches:
                res_list.append(f"Line {match[0]}: {match[1]}")
            res_list.append(f'[End of matches for "{search_term}" in {file_path}]')
        else:
            res_list.append(f'[No matches found for "{search_term}" in {file_path}]')

        extra = {"type": "search", "symbol": search_term, "lines": [i[0] - 1 for i in matches]} if matches else None
        self.resource.report(file_path, "path", extra=extra)
        return "\n".join(res_list)

    def find_file(self, file_name: str, dir_path: str = "./") -> str:
        """Finds all files with the given name in the specified directory.

        Args:
            file_name: str: The name of the file to find.
            dir_path: str: The path to the directory to search.
        """
        file_name = self._try_fix_path(file_name)
        dir_path = self._try_fix_path(dir_path)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Directory {dir_path} not found")

        matches = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if str(file_name) in file:
                    matches.append(Path(root) / file)

        res_list = []
        if matches:
            res_list.append(f'[Found {len(matches)} matches for "{file_name}" in {dir_path}]')
            for match in matches:
                res_list.append(f"{match}")
            res_list.append(f'[End of matches for "{file_name}" in {dir_path}]')
        else:
            res_list.append(f'[No matches found for "{file_name}" in {dir_path}]')
        return "\n".join(res_list)

    def _try_fix_path(self, path: Union[Path, str]) -> Path:
        """Tries to fix the path if it is not absolute."""
        if not isinstance(path, Path):
            path = Path(path)
        if not path.is_absolute():
            path = self.working_dir / path
        return path

    @staticmethod
    async def similarity_search(query: str, path: Union[str, Path]) -> List[str]:
        """Given a filename or a pathname, performs a similarity search for a given query across the specified file or path.

        This method searches the index repository for the provided query, classifying the specified
        files or paths. It performs a search on each cluster of files and handles non-indexed files
        separately, merging results from structured indices with any direct results from non-indexed files.
        This function call does not depend on other functions.

        Args:
            query (str): The search query string to look for in the indexed files.
            path (Union[str, Path]): A pathname or filename to search within.

        Returns:
            List[str]: A list of results as strings, containing the text from the merged results
                        and any direct results from non-indexed files.

        Example:
            >>> query = "The problem to be analyzed from the document"
            >>> file_or_path = "The pathname or filename you want to search within"
            >>> texts: List[str] = await Editor.similarity_search(query=query, path=file_or_path)
            >>> print(texts)
        """
        try:
            from metagpt.tools.libs.index_repo import IndexRepo

            return await IndexRepo.cross_repo_search(query=query, file_or_path=path)
        except ImportError:
            raise ImportError("To use the similarity search, you need to install the RAG module.")

    @staticmethod
    def is_large_file(content: str, mix_token_count: int = 0) -> bool:
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(content))
        mix_token_count = mix_token_count or DEFAULT_MIN_TOKEN_COUNT
        return token_count >= mix_token_count

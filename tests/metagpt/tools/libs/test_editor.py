import os
import shutil
from pathlib import Path

import pytest

from metagpt.const import TEST_DATA_PATH
from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.index_repo import (
    CHATS_INDEX_ROOT,
    CHATS_ROOT,
    DEFAULT_MIN_TOKEN_COUNT,
    UPLOAD_ROOT,
    IndexRepo,
)
from metagpt.utils.common import list_files

TEST_FILE_CONTENT = """
# this is line one
def test_function_for_fm():
    "some docstring"
    a = 1
    b = 2
    c = 3
    # this is the 7th line
""".strip()

WINDOW = 200


@pytest.fixture
def temp_file_path(tmp_path):
    assert tmp_path is not None
    temp_file_path = tmp_path / "a.txt"
    yield temp_file_path
    temp_file_path.unlink()


@pytest.fixture
def temp_py_file(tmp_path):
    assert tmp_path is not None
    temp_file_path = tmp_path / "test_script_for_editor.py"
    temp_file_path.write_text(TEST_FILE_CONTENT)
    yield temp_file_path
    temp_file_path.unlink()


@pytest.fixture
def empty_file(tmp_path):
    assert tmp_path is not None
    temp_file_path = tmp_path / "test_script_empty_file_for_editor.py"
    temp_file_path.write_text("")
    yield temp_file_path
    temp_file_path.unlink()


EXPECTED_CONTENT_AFTER_REPLACE = """
# this is line one
def test_function_for_fm():
    # This is the new line A replacing lines 3 to 5.
    # This is the new line B.
    c = 3
    # this is the 7th line
""".strip()


def test_replace_content(temp_py_file):
    editor = Editor()
    editor._edit_file_impl(
        file_name=temp_py_file,
        start=3,
        end=5,
        content="    # This is the new line A replacing lines 3 to 5.\n    # This is the new line B.",
        is_insert=False,
        is_append=False,
    )
    with open(temp_py_file, "r") as f:
        new_content = f.read()
    assert new_content.strip() == EXPECTED_CONTENT_AFTER_REPLACE.strip()


EXPECTED_CONTENT_AFTER_DELETE = """
# this is line one
def test_function_for_fm():

    c = 3
    # this is the 7th line
""".strip()


def test_delete_content(temp_py_file):
    editor = Editor()
    editor._edit_file_impl(
        file_name=temp_py_file,
        start=3,
        end=5,
        content="",
        is_insert=False,
        is_append=False,
    )
    with open(temp_py_file, "r") as f:
        new_content = f.read()
    assert new_content.strip() == EXPECTED_CONTENT_AFTER_DELETE.strip()


EXPECTED_CONTENT_AFTER_INSERT = """
# this is line one
def test_function_for_fm():
    # This is the new line to be inserted, at line 3
    "some docstring"
    a = 1
    b = 2
    c = 3
    # this is the 7th line
""".strip()


def test_insert_content(temp_py_file):
    editor = Editor(enable_auto_lint=True)
    editor.insert_content_at_line(
        file_name=temp_py_file,
        line_number=3,
        insert_content="    # This is the new line to be inserted, at line 3",
    )
    with open(temp_py_file, "r") as f:
        new_content = f.read()
    assert new_content.strip() == EXPECTED_CONTENT_AFTER_INSERT.strip()


@pytest.mark.parametrize(
    "filename",
    [
        TEST_DATA_PATH / "output_parser/1.md",
        TEST_DATA_PATH / "search/serper-metagpt-8.json",
        TEST_DATA_PATH / "audio/hello.mp3",
        TEST_DATA_PATH / "code/python/1.py",
        TEST_DATA_PATH / "code/js/1.js",
        TEST_DATA_PATH / "ui/1b.png.html",
        TEST_DATA_PATH / "movie/trailer.mp4",
    ],
)
@pytest.mark.asyncio
async def test_read_files(filename):
    editor = Editor()
    file_block = await editor.read(filename)
    assert file_block
    assert file_block.file_path
    if filename.suffix not in [".png", ".mp3", ".mp4"]:
        assert file_block.block_content


def _numbered_test_lines(start, end) -> str:
    return ("\n".join(f"{i}|" for i in range(start, end + 1))) + "\n"


def _generate_test_file_with_lines(temp_path, num_lines) -> str:
    file_path = temp_path / "test_file.py"
    file_path.write_text("\n" * num_lines)
    return file_path


def _generate_ruby_test_file_with_lines(temp_path, num_lines) -> str:
    file_path = temp_path / "test_file.rb"
    file_path.write_text("\n" * num_lines)
    return file_path


def _calculate_window_bounds(current_line, total_lines, window_size):
    half_window = window_size // 2
    if current_line - half_window < 0:
        start = 1
        end = window_size
    else:
        start = current_line - half_window
        end = current_line + half_window
    return start, end


def test_open_file_unexist_path():
    editor = Editor()
    with pytest.raises(FileNotFoundError):
        editor.open_file("/unexist/path/a.txt")


def test_open_file(temp_file_path):
    editor = Editor()
    temp_file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

    result = editor.open_file(str(temp_file_path))

    assert result is not None
    expected = (
        f"[File: {temp_file_path} (5 lines total)]\n"
        "(this is the beginning of the file)\n"
        "001|Line 1\n"
        "002|Line 2\n"
        "003|Line 3\n"
        "004|Line 4\n"
        "005|Line 5\n"
        "(this is the end of the file)"
    )
    assert result.split("\n") == expected.split("\n")


def test_open_file_with_indentation(temp_file_path):
    editor = Editor()
    temp_file_path.write_text("Line 1\n    Line 2\nLine 3\nLine 4\nLine 5")

    result = editor.open_file(str(temp_file_path))
    assert result is not None
    expected = (
        f"[File: {temp_file_path} (5 lines total)]\n"
        "(this is the beginning of the file)\n"
        "001|Line 1\n"
        "002|    Line 2\n"
        "003|Line 3\n"
        "004|Line 4\n"
        "005|Line 5\n"
        "(this is the end of the file)"
    )
    assert result.split("\n") == expected.split("\n")


def test_open_file_long(temp_file_path):
    editor = Editor()
    content = "\n".join([f"Line {i}" for i in range(1, 1001)])
    temp_file_path.write_text(content)

    result = editor.open_file(str(temp_file_path), 1, 50)
    assert result is not None
    expected = f"[File: {temp_file_path} (1000 lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, 51):
        expected += f"{i:03d}|Line {i}\n"
    expected += "(950 more lines below)"
    assert result.split("\n") == expected.split("\n")


def test_open_file_long_with_lineno(temp_file_path):
    editor = Editor()
    content = "\n".join([f"Line {i}" for i in range(1, 1001)])
    temp_file_path.write_text(content)

    cur_line = 300

    result = editor.open_file(str(temp_file_path), cur_line)
    assert result is not None
    expected = f"[File: {temp_file_path} (1000 lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, 1000, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == 1000:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({1000 - end} more lines below)"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_create_file(temp_file_path):
    editor = Editor()
    result = await editor.create_file(str(temp_file_path))

    expected = f"[File {temp_file_path} created.]"
    assert result.split("\n") == expected.split("\n")


def test_goto_line(temp_file_path):
    editor = Editor()
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    result = editor.open_file(str(temp_file_path))
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, WINDOW + 1):
        expected += f"{i:03d}|Line {i}\n"
    expected += f"({total_lines - WINDOW} more lines below)"
    assert result.split("\n") == expected.split("\n")

    result = editor.goto_line(500)

    assert result is not None

    cur_line = 500
    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")


def test_goto_line_negative(temp_file_path):
    editor = Editor()
    content = "\n".join([f"Line {i}" for i in range(1, 5)])
    temp_file_path.write_text(content)

    editor.open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        editor.goto_line(-1)


def test_goto_line_out_of_bound(temp_file_path):
    editor = Editor()
    content = "\n".join([f"Line {i}" for i in range(1, 5)])
    temp_file_path.write_text(content)

    editor.open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        editor.goto_line(100)


def test_scroll_down(temp_file_path):
    editor = Editor()
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)
    result = editor.open_file(str(temp_file_path))
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")

    result = editor.scroll_down()

    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(WINDOW + 1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")


def test_scroll_up(temp_file_path):
    editor = Editor()
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    cur_line = 500

    result = editor.open_file(str(temp_file_path), cur_line)
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"

    assert result.split("\n") == expected.split("\n")
    result = editor.scroll_up()
    assert result is not None

    cur_line = cur_line - WINDOW

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    print(result)
    print(expected)
    assert result.split("\n") == expected.split("\n")


def test_scroll_down_edge(temp_file_path):
    editor = Editor()
    content = "\n".join([f"Line {i}" for i in range(1, 10)])
    temp_file_path.write_text(content)

    result = editor.open_file(str(temp_file_path))
    assert result is not None

    expected = f"[File: {temp_file_path} (9 lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, 10):
        expected += f"{i:03d}|Line {i}\n"
    expected += "(this is the end of the file)"

    result = editor.scroll_down()
    assert result is not None

    assert result.split("\n") == expected.split("\n")


def test_print_window_internal(temp_file_path):
    editor = Editor()
    editor.create_file(str(temp_file_path))
    with open(temp_file_path, "w") as file:
        for i in range(1, 101):
            file.write(f"Line `{i}`\n")

    current_line = 50
    window = 2

    result = editor._print_window(temp_file_path, current_line, window)
    expected = "(48 more lines above)\n" "049|Line `49`\n" "050|Line `50`\n" "051|Line `51`\n" "(49 more lines below)"
    assert result == expected


def test_open_file_large_line_number(temp_file_path):
    editor = Editor()
    editor.create_file(str(temp_file_path))
    with open(temp_file_path, "w") as file:
        for i in range(1, 1000):
            file.write(f"Line `{i}`\n")

    current_line = 800
    window = 100

    result = editor.open_file(str(temp_file_path), current_line, window)

    expected = f"[File: {temp_file_path} (999 lines total)]\n"
    expected += "(749 more lines above)\n"
    for i in range(750, 850 + 1):
        expected += f"{i}|Line `{i}`\n"
    expected += "(149 more lines below)"
    assert result == expected


def test_open_file_large_line_number_consecutive_diff_window(temp_file_path):
    editor = Editor()
    editor.create_file(str(temp_file_path))
    total_lines = 1000
    with open(temp_file_path, "w") as file:
        for i in range(1, total_lines + 1):
            file.write(f"Line `{i}`\n")

    current_line = 800
    cur_window = 300

    result = editor.open_file(str(temp_file_path), current_line, cur_window)

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(current_line, total_lines, cur_window)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(current_line - cur_window // 2, current_line + cur_window // 2 + 1):
        expected += f"{i}|Line `{i}`\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result == expected

    current_line = current_line - WINDOW

    result = editor.scroll_up()

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(current_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line `{i}`\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")


EXPECTED_CONTENT_AFTER_REPLACE_TEXT = """
# this is line one
def test_function_for_fm():
    "some docstring"
    a = 1
    b = 9
    c = 3
    # this is the 7th line
""".strip()


def test_edit_file_by_replace(temp_py_file):
    editor = Editor()
    editor.edit_file_by_replace(
        file_name=str(temp_py_file),
        first_replaced_line_number=5,
        first_replaced_line_content="    b = 2",
        new_content="    b = 9",
        last_replaced_line_number=5,
        last_replaced_line_content="    b = 2",
    )
    with open(temp_py_file, "r") as f:
        new_content = f.read()
    assert new_content.strip() == EXPECTED_CONTENT_AFTER_REPLACE_TEXT.strip()


MISMATCH_ERROR = """
Error: The `first_replaced_line_number` does not match the `first_replaced_line_content`. Please correct the parameters.
The `first_replaced_line_number` is 5 and the corresponding content is "    b = 2".
But the `first_replaced_line_content ` is "".
The content around the specified line is:
The 002 line is "def test_function_for_fm():"
The 003 line is "    "some docstring""
The 004 line is "    a = 1"
The 005 line is "    b = 2"
The 006 line is "    c = 3"
The 007 line is "    # this is the 7th line"
Pay attention to the new content. Ensure that it aligns with the new parameters.
Error: The `last_replaced_line_number` does not match the `last_replaced_line_content`. Please correct the parameters.
The `last_replaced_line_number` is 5 and the corresponding content is "    b = 2".
But the `last_replaced_line_content ` is "".
The content around the specified line is:
The 002 line is "def test_function_for_fm():"
The 003 line is "    "some docstring""
The 004 line is "    a = 1"
The 005 line is "    b = 2"
The 006 line is "    c = 3"
The 007 line is "    # this is the 7th line"
Pay attention to the new content. Ensure that it aligns with the new parameters.
""".strip()


def test_edit_file_by_replace_mismatch(temp_py_file):
    editor = Editor()
    with pytest.raises(ValueError) as match_error:
        editor.edit_file_by_replace(
            file_name=str(temp_py_file),
            first_replaced_line_number=5,
            first_replaced_line_content="",
            new_content="    b = 9",
            last_replaced_line_number=5,
            last_replaced_line_content="",
        )
    assert str(match_error.value).strip() == MISMATCH_ERROR.strip()


def test_append_file(temp_file_path):
    editor = Editor()
    # 写入初始内容
    initial_content = "Line 1\nLine 2\nLine 3\n"
    temp_file_path.write_text(initial_content)

    # 追加内容到文件
    append_content = "Line 4\nLine 5\n"

    result = editor.append_file(str(temp_file_path), append_content)

    # 预期内容
    expected_content = initial_content + append_content

    # 读取文件并断言内容与预期一致
    with open(temp_file_path, "r") as f:
        new_content = f.read()
    assert new_content == expected_content

    # 输出的预期结果
    expected_output = (
        f"[File: {temp_file_path.resolve()} (5 lines total after edit)]\n"
        "(this is the beginning of the file)\n"
        "001|Line 1\n"
        "002|Line 2\n"
        "003|Line 3\n"
        "004|Line 4\n"
        "005|Line 5\n"
        "(this is the end of the file)\n"
        "[File updated (edited at line 3)]."
    )

    assert result.split("\n") == expected_output.split("\n")


def test_search_dir(tmp_path):
    editor = Editor()
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    # Create some files with specific content
    (dir_path / "file1.txt").write_text("This is a test file with some content.")
    (dir_path / "file2.txt").write_text("Another file with different content.")
    sub_dir = dir_path / "sub_dir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("This file is inside a sub directory with some content.")

    search_term = "some content"

    result = editor.search_dir(search_term, str(dir_path))

    assert "file1.txt" in result
    assert "file3.txt" in result
    assert "Another file with different content." not in result


def test_search_dir_in_default_dir(tmp_path):
    editor = Editor()
    dir_path = editor.working_dir / "test_dir"
    dir_path.mkdir(exist_ok=True)

    # Create some files with specific content
    (dir_path / "file1.txt").write_text("This is a test file with some content.")
    (dir_path / "file2.txt").write_text("Another file with different content.")
    sub_dir = dir_path / "sub_dir"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "file3.txt").write_text("This file is inside a sub directory with some content.")

    search_term = "some content"

    result = editor.search_dir(search_term)

    assert "file1.txt" in result
    assert "file3.txt" in result
    assert "Another file with different content." not in result


def test_search_file(temp_file_path):
    editor = Editor()
    file_path = temp_file_path
    file_path.write_text("This is a test file with some content.\nAnother line with more content.")

    search_term = "some content"

    result = editor.search_file(search_term, str(file_path))

    assert "Line 1: This is a test file with some content." in result
    assert "Line 2: Another line with more content." not in result


def test_find_file(tmp_path):
    editor = Editor()
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    # Create some files with specific names
    (dir_path / "file1.txt").write_text("Content of file 1.")
    (dir_path / "file2.txt").write_text("Content of file 2.")
    sub_dir = dir_path / "sub_dir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("Content of file 3.")

    file_name = "file1.txt"

    result = editor.find_file(file_name, str(dir_path))

    assert "file1.txt" in result
    assert "file2.txt" not in result
    assert "file3.txt" not in result


# Test data for _append_impl method
TEST_LINES = ["First line\n", "Second line\n", "Third line\n"]

NEW_CONTENT = "Appended line\n"

EXPECTED_APPEND_NON_EMPTY_FILE = ["First line\n", "Second line\n", "Third line\n", "Appended line\n"]

EXPECTED_APPEND_EMPTY_FILE = ["Appended line\n"]


def test_append_non_empty_file():
    editor = Editor()
    lines = TEST_LINES.copy()
    content, n_added_lines = editor._append_impl(lines, NEW_CONTENT)

    assert content.splitlines(keepends=True) == EXPECTED_APPEND_NON_EMPTY_FILE
    assert n_added_lines == 1


def test_append_empty_file():
    editor = Editor()
    lines = []
    content, n_added_lines = editor._append_impl(lines, NEW_CONTENT)

    assert content.splitlines(keepends=True) == EXPECTED_APPEND_EMPTY_FILE
    assert n_added_lines == 1


def test_append_to_single_empty_line_file():
    editor = Editor()
    lines = [""]
    content, n_added_lines = editor._append_impl(lines, NEW_CONTENT)

    assert content.splitlines(keepends=True) == EXPECTED_APPEND_EMPTY_FILE
    assert n_added_lines == 1


async def mock_index_repo():
    chat_id = "1"
    chat_path = Path(CHATS_ROOT) / chat_id
    chat_path.mkdir(parents=True, exist_ok=True)
    src_path = TEST_DATA_PATH / "requirements"
    command = f"cp -rf {str(src_path)} {str(chat_path)}"
    os.system(command)
    filenames = list_files(chat_path)
    chat_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    chat_repo = IndexRepo(
        persist_path=str(Path(CHATS_INDEX_ROOT) / chat_id), root_path=str(chat_path), min_token_count=0
    )
    await chat_repo.add(chat_files)
    assert chat_files

    Path(UPLOAD_ROOT).mkdir(parents=True, exist_ok=True)
    command = f"cp -rf {str(src_path)} {str(UPLOAD_ROOT)}"
    os.system(command)
    filenames = list_files(UPLOAD_ROOT)
    uploads_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    assert uploads_files

    filenames = list_files(src_path)
    other_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    assert other_files

    return chat_path, UPLOAD_ROOT, src_path


@pytest.mark.skip
@pytest.mark.asyncio
async def test_index_repo():
    # mock data
    chat_path, upload_path, src_path = await mock_index_repo()

    editor = Editor()
    rsp = await editor.similarity_search(query="业务线", path=chat_path)
    assert rsp
    rsp = await editor.similarity_search(query="业务线", path=upload_path)
    assert rsp
    rsp = await editor.similarity_search(query="业务线", path=src_path)
    assert rsp

    shutil.rmtree(CHATS_ROOT)
    shutil.rmtree(UPLOAD_ROOT)


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "filename"),
    [
        (
            "In this document, who are the legal representatives of both parties?",
            TEST_DATA_PATH / "pdf/20210709逗你学云豆付费课程协议.pdf",
        ),
        (
            "What is the short name of the company in this document?",
            TEST_DATA_PATH / "pdf/company_stock_code.pdf",
        ),
        ("平安创新推出中国版的什么模式，将差异化的医疗健康服务与作为支付方的金融业务无缝结合", TEST_DATA_PATH / "pdf/9112674.pdf"),
        (
            "What principle is introduced by the author to explain the conditions necessary for the emergence of complexity?",
            TEST_DATA_PATH / "pdf/9781444323498.ch2_1.pdf",
        ),
        ("行高的继承性的代码示例是？", TEST_DATA_PATH / "pdf/02-CSS.pdf"),
    ],
)
async def test_similarity_search(query, filename):
    filename = Path(filename)
    save_to = Path(UPLOAD_ROOT) / filename.name
    save_to.parent.mkdir(parents=True, exist_ok=True)
    os.system(f"cp {str(filename)} {str(save_to)}")

    editor = Editor()
    rsp = await editor.similarity_search(query=query, path=save_to)
    assert rsp

    save_to.unlink(missing_ok=True)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_read():
    editor = Editor()
    filename = TEST_DATA_PATH / "pdf/9112674.pdf"
    content = await editor.read(str(filename))
    size = filename.stat().st_size
    assert "similarity_search" in content.block_content and size > 5 * DEFAULT_MIN_TOKEN_COUNT


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

import contextlib
import io

import pytest

from metagpt.const import TEST_DATA_PATH
from metagpt.tools.libs.editor import WINDOW, Editor

TEST_FILE_CONTENT = """
# this is line one
def test_function_for_fm():
    "some docstring"
    a = 1
    b = 2
    c = 3
    # this is the 7th line
""".strip()

TEST_FILE_PATH = TEST_DATA_PATH / "tools/test_script_for_editor.py"


@pytest.fixture
def test_file():
    with open(TEST_FILE_PATH, "w") as f:
        f.write(TEST_FILE_CONTENT)
    yield
    with open(TEST_FILE_PATH, "w") as f:
        f.write("")


EXPECTED_CONTENT_AFTER_REPLACE = """
# this is line one
def test_function_for_fm():
    # This is the new line A replacing lines 3 to 5.
    # This is the new line B.
    c = 3
    # this is the 7th line
""".strip()


@pytest.mark.skip
def test_replace_content(test_file):
    Editor().write_content(
        file_path=str(TEST_FILE_PATH),
        start_line=3,
        end_line=5,
        new_block_content="    # This is the new line A replacing lines 3 to 5.\n    # This is the new line B.",
    )
    with open(TEST_FILE_PATH, "r") as f:
        new_content = f.read()
    assert new_content == EXPECTED_CONTENT_AFTER_REPLACE


EXPECTED_CONTENT_AFTER_DELETE = """
# this is line one
def test_function_for_fm():
    c = 3
    # this is the 7th line
""".strip()


def test_delete_content(test_file):
    Editor().write_content(file_path=str(TEST_FILE_PATH), start_line=3, end_line=5)
    with open(TEST_FILE_PATH, "r") as f:
        new_content = f.read()
    assert new_content == EXPECTED_CONTENT_AFTER_DELETE


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


@pytest.mark.skip
def test_insert_content(test_file):
    Editor().write_content(
        file_path=str(TEST_FILE_PATH),
        start_line=3,
        end_line=-1,
        new_block_content="    # This is the new line to be inserted, at line 3",
    )
    with open(TEST_FILE_PATH, "r") as f:
        new_content = f.read()
    assert new_content == EXPECTED_CONTENT_AFTER_INSERT


@pytest.mark.parametrize(
    "filename",
    [
        TEST_DATA_PATH / "requirements/1.txt",
        TEST_DATA_PATH / "requirements/1.json",
        TEST_DATA_PATH / "requirements/1.constraint.md",
        TEST_DATA_PATH / "requirements/pic/1.png",
        TEST_DATA_PATH / "docx_for_test.docx",
        TEST_DATA_PATH / "requirements/2.pdf",
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


@pytest.fixture(autouse=True)
def reset_current_file():
    global CURRENT_FILE
    CURRENT_FILE = None


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


@pytest.mark.asyncio
async def test_open_file_unexist_path():
    editor = Editor()
    with pytest.raises(FileNotFoundError):
        editor.open_file("/unexist/path/a.txt")


@pytest.mark.asyncio
async def test_open_file(tmp_path):
    editor = Editor()
    assert tmp_path is not None
    temp_file_path = tmp_path / "a.txt"
    temp_file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = (
        f"[File: {temp_file_path} (5 lines total)]\n"
        "(this is the beginning of the file)\n"
        "1|Line 1\n"
        "2|Line 2\n"
        "3|Line 3\n"
        "4|Line 4\n"
        "5|Line 5\n"
        "(this is the end of the file)\n"
    )
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_open_file_with_indentation(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    temp_file_path.write_text("Line 1\n    Line 2\nLine 3\nLine 4\nLine 5")

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = (
        f"[File: {temp_file_path} (5 lines total)]\n"
        "(this is the beginning of the file)\n"
        "1|Line 1\n"
        "2|    Line 2\n"
        "3|Line 3\n"
        "4|Line 4\n"
        "5|Line 5\n"
        "(this is the end of the file)\n"
    )
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_open_file_long(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    content = "\n".join([f"Line {i}" for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path), 1, 50)
        result = buf.getvalue()
    assert result is not None
    expected = f"[File: {temp_file_path} (1000 lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, 51):
        expected += f"{i}|Line {i}\n"
    expected += "(950 more lines below)\n"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_open_file_long_with_lineno(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    content = "\n".join([f"Line {i}" for i in range(1, 1001)])
    temp_file_path.write_text(content)

    cur_line = 100

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path), cur_line)
        result = buf.getvalue()
    assert result is not None
    expected = f"[File: {temp_file_path} (1000 lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, 1000, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == 1000:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({1000 - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_create_file_unexist_path():
    editor = Editor()
    with pytest.raises(FileNotFoundError):
        editor.create_file("/unexist/path/a.txt")


@pytest.mark.asyncio
async def test_create_file(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.create_file(str(temp_file_path))
        result = buf.getvalue()

    expected = (
        f"[File: {temp_file_path} (1 lines total)]\n"
        "(this is the beginning of the file)\n"
        "1|\n"
        "(this is the end of the file)\n"
        f"[File {temp_file_path} created.]\n"
    )
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_goto_line(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, WINDOW + 1):
        expected += f"{i}|Line {i}\n"
    expected += f"({total_lines - WINDOW} more lines below)\n"
    assert result.split("\n") == expected.split("\n")

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.goto_line(500)
        result = buf.getvalue()
    assert result is not None

    cur_line = 500
    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_goto_line_negative(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    content = "\n".join([f"Line {i}" for i in range(1, 5)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        editor.goto_line(-1)


@pytest.mark.asyncio
async def test_goto_line_out_of_bound(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    content = "\n".join([f"Line {i}" for i in range(1, 5)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        editor.goto_line(100)


@pytest.mark.asyncio
async def test_scroll_down(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.scroll_down()
        result = buf.getvalue()
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(WINDOW + 1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_scroll_up(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    cur_line = 300
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path), cur_line)
        result = buf.getvalue()
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.scroll_up()
        result = buf.getvalue()
    assert result is not None

    cur_line = cur_line - WINDOW

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)\n"
    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_scroll_down_edge(tmp_path):
    editor = Editor()
    temp_file_path = tmp_path / "a.txt"
    content = "\n".join([f"Line {i}" for i in range(1, 10)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f"[File: {temp_file_path} (9 lines total)]\n"
    expected += "(this is the beginning of the file)\n"
    for i in range(1, 10):
        expected += f"{i}|Line {i}\n"
    expected += "(this is the end of the file)\n"

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.scroll_down()
        result = buf.getvalue()
    assert result is not None

    assert result.split("\n") == expected.split("\n")


@pytest.mark.asyncio
async def test_print_window_internal(tmp_path):
    editor = Editor()
    test_file_path = tmp_path / "a.txt"
    await editor.create_file(str(test_file_path))
    editor.open_file(str(test_file_path))
    with open(test_file_path, "w") as file:
        for i in range(1, 101):
            file.write(f"Line `{i}`\n")

    current_line = 50
    window = 2

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor._print_window(str(test_file_path), current_line, window, return_str=False)
        result = buf.getvalue()
    expected = "(48 more lines above)\n" "49|Line `49`\n" "50|Line `50`\n" "51|Line `51`\n" "(49 more lines below)\n"
    assert result == expected


@pytest.mark.asyncio
async def test_open_file_large_line_number(tmp_path):
    editor = Editor()
    test_file_path = tmp_path / "a.txt"
    editor.create_file(str(test_file_path))
    editor.open_file(str(test_file_path))
    with open(test_file_path, "w") as file:
        for i in range(1, 1000):
            file.write(f"Line `{i}`\n")

    current_line = 800
    window = 100

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(test_file_path), current_line, window)
        result = buf.getvalue()
    expected = f"[File: {test_file_path} (999 lines total)]\n"
    expected += "(749 more lines above)\n"
    for i in range(750, 850 + 1):
        expected += f"{i}|Line `{i}`\n"
    expected += "(149 more lines below)\n"
    assert result == expected


@pytest.mark.asyncio
async def test_open_file_large_line_number_consecutive_diff_window(tmp_path):
    editor = Editor()
    test_file_path = tmp_path / "a.txt"
    editor.create_file(str(test_file_path))
    editor.open_file(str(test_file_path))
    total_lines = 1000
    with open(test_file_path, "w") as file:
        for i in range(1, total_lines + 1):
            file.write(f"Line `{i}`\n")

    current_line = 800
    cur_window = 300

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.open_file(str(test_file_path), current_line, cur_window)
        result = buf.getvalue()
    expected = f"[File: {test_file_path} ({total_lines} lines total)]\n"
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
        expected += f"({total_lines - end} more lines below)\n"
    assert result == expected

    current_line = current_line - WINDOW
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            editor.scroll_up()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

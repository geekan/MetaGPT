import pytest

from metagpt.const import TEST_DATA_PATH
from metagpt.tools.libs.editor import Editor, FileBlock

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


EXPECTED_SEARCHED_BLOCK = FileBlock(
    file_path=str(TEST_FILE_PATH),
    block_content='001|# this is line one\n002|def test_function_for_fm():\n003|    "some docstring"\n004|    a = 1\n005|    b = 2\n',
    block_start_line=1,
    block_end_line=5,
    symbol="def test_function_for_fm",
    symbol_line=2,
)


def test_search_content(test_file):
    block = Editor().search_content("def test_function_for_fm", root_path=TEST_DATA_PATH, window=3)
    assert block == EXPECTED_SEARCHED_BLOCK


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


@pytest.mark.skip
def test_new_content_wrong_indentation(test_file):
    msg = Editor().write_content(
        file_path=str(TEST_FILE_PATH),
        start_line=3,
        end_line=-1,
        new_block_content="    This is the new line to be inserted, at line 3",  # omit # should throw a syntax error
    )
    assert "failed" in msg


@pytest.mark.skip
def test_new_content_format_issue(test_file):
    msg = Editor().write_content(
        file_path=str(TEST_FILE_PATH),
        start_line=3,
        end_line=-1,
        new_block_content="    # This is the new line to be inserted, at line 3  ",  # trailing spaces are format issue only, and should not throw an error
    )
    assert "failed" not in msg


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


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

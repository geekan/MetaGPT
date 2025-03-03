import tempfile
from pathlib import Path

import pytest

from metagpt.tools.libs.linter import Linter, LintResult


def test_linter_initialization():
    linter = Linter(encoding="utf-8", root="/test/root")
    assert linter.encoding == "utf-8"
    assert linter.root == "/test/root"
    assert "python" in linter.languages
    assert callable(linter.languages["python"])


def test_get_abs_fname():
    linter = Linter(root="/test/root")
    abs_path = linter.get_abs_fname("test_file.py")
    assert abs_path == linter.get_rel_fname("test_file.py")


def test_py_lint():
    linter = Linter()
    code = "print('Hello, World!')"
    test_file_path = str(Path(__file__).resolve())
    result = linter.py_lint(test_file_path, test_file_path, code)
    assert result is None  # No errors expected for valid Python code


def test_lint_with_python_file():
    linter = Linter()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=True) as temp_file:
        temp_file.write(b"def hello():\nprint('Hello')\n")  # IndentationError
        temp_file.flush()
        result = linter.lint(temp_file.name)
        assert isinstance(result, LintResult)
        assert "IndentationError" in result.text
        assert len(result.lines) > 0


def test_lint_with_unsupported_language():
    linter = Linter()
    with tempfile.NamedTemporaryFile(suffix=".unsupported", delete=True) as temp_file:
        temp_file.write(b"This is unsupported code.")
        temp_file.flush()

        result = linter.lint(temp_file.name)
        assert result is None  # Unsupported language should return None


def test_run_cmd():
    linter = Linter()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=True) as temp_file:
        temp_file.write(b"print('Hello, World!')\n")
        temp_file.flush()

        result = linter.run_cmd("flake8", temp_file.name, "print('Hello, World!')")
        # Since flake8 might not be installed in the test environment, we just ensure no exception is raised
        assert result is None or isinstance(result, LintResult)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

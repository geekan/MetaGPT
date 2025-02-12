import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from metagpt.tools.libs.cr import CodeReview


class MockFile:
    def __init__(self, content):
        self.content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def read(self):
        return self.content


@pytest.mark.asyncio
class TestCodeReview:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        """Fixture to initialize the CodeReview instance."""
        self.cr = CodeReview()

    @patch("aiofiles.open", new_callable=MagicMock)
    @patch("metagpt.utils.report.EditorReporter.async_report", new_callable=AsyncMock)
    @patch("metagpt.ext.cr.actions.code_review.CodeReview.run", new_callable=AsyncMock)
    async def test_review(self, mock_run, mock_report, mock_aiofiles_open):
        """Test the review method with a local patch file."""
        # mock patch_content
        patch_content = """diff --git a/test.py b/test.py
index 1234567..89abcde 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def foo():
-    print("Hello")
+    print("World")
-    print("Another line")
+    print("Another modified line")"""

        # mock point file content
        point_file_content = json.dumps([{"id": 1, "description": "Test point"}])

        mock_patch_file = MockFile(patch_content)
        mock_point_file = MockFile(point_file_content)
        mock_aiofiles_open.side_effect = [mock_patch_file, mock_point_file]

        mock_run.return_value = [{"comment": "Fix this line"}]

        # run
        result = await self.cr.review(patch_path="test.patch", output_file="output.json")

        # assert
        assert "The number of defects: 1" in result
        mock_run.assert_called_once()
        mock_report.assert_called()

    @patch("aiofiles.open", new_callable=MagicMock)
    @patch("metagpt.ext.cr.actions.modify_code.ModifyCode.run", new_callable=AsyncMock)
    async def test_fix(self, mock_run, mock_aiofiles_open):
        """Test the fix method."""
        patch_content = """diff --git a/test.py b/test.py
index 1234567..89abcde 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def foo():
-    print("Hello")
+    print("World")
-    print("Another line")
+    print("Another modified line")"""

        cr_file_content = json.dumps([{"comment": "Fix this line"}])

        # mock file obj
        mock_path_file = MockFile(patch_content)
        mock_cr_file = MockFile(cr_file_content)
        mock_aiofiles_open.side_effect = [mock_path_file, mock_cr_file]

        # run fix
        result = await self.cr.fix(patch_path="test.patch", cr_file="cr.json", output_dir="output")

        # assert
        assert "The fixed patch files store in output" in result
        mock_run.assert_called_once()

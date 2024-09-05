import difflib
import json
from pathlib import Path
from typing import Optional

import aiofiles
from bs4 import BeautifulSoup
from unidiff import PatchSet

import metagpt.ext.cr
from metagpt.ext.cr.actions.code_review import CodeReview as CodeReview_
from metagpt.ext.cr.actions.modify_code import ModifyCode
from metagpt.ext.cr.utils.schema import Point
from metagpt.tools.libs.browser import Browser
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.report import EditorReporter


@register_tool(tags=["codereview"], include_functions=["review", "fix"])
class CodeReview:
    """Review and fix the patch content from the pull request URL or a file."""

    async def review(
        self,
        patch_path: str,
        output_file: str,
        point_file: Optional[str] = None,
    ) -> str:
        """Review a PR and save code review comments.

        Notes:
            If the user does not specify an output path, saved it using a relative path in the current working directory.

        Args:
            patch_path: The local path of the patch file or the URL of the pull request.
            output_file: Output file path where code review comments will be saved.
            point_file: File path for specifying code review points. If not specified, this parameter does not need to be passed.

        Examples:

            >>> cr = CodeReview()
            >>> await cr.review(patch_path="https://github.com/geekan/MetaGPT/pull/136", output_file="cr/MetaGPT_136.json")
            >>> await cr.review(patch_path="/data/uploads/dev-master.diff", output_file="cr/dev-master.json")
            >>> await cr.review(patch_path="/data/uploads/main.py", output_file="cr/main.json")
        """
        patch = await self._get_patch_content(patch_path)
        point_file = point_file if point_file else Path(metagpt.ext.cr.__file__).parent / "points.json"
        await EditorReporter().async_report(str(point_file), "path")
        async with aiofiles.open(point_file, "rb") as f:
            cr_point_content = await f.read()
            cr_points = [Point(**i) for i in json.loads(cr_point_content)]
        try:
            comments = await CodeReview_().run(patch, cr_points, output_file)
        except ValueError as e:
            return str(e)
        return f"The number of defects: {len(comments)}, the comments are stored in {output_file}, and the checkpoints are stored in {str(point_file)}"

    async def fix(
        self,
        patch_path: str,
        cr_file: str,
        output_dir: str,
    ) -> str:
        """Fix the patch content based on code review comments.

        Args:
            patch_path: The local path of the patch file or the url of the pull request.
            cr_file: File path where code review comments are stored.
            output_dir: File path where code review comments are stored.
        """
        patch = await self._get_patch_content(patch_path)
        async with aiofiles.open(cr_file, "r", encoding="utf-8") as f:
            comments = json.loads(await f.read())
        await ModifyCode(pr="").run(patch, comments, output_dir)
        return f"The fixed patch files store in {output_dir}"

    async def _get_patch_content(self, patch_path):
        if patch_path.startswith(("https://", "http://")):
            # async with aiohttp.ClientSession(trust_env=True) as client:
            #     async with client.get(f"{patch_path}.diff", ) as resp:
            #         patch_file_content = await resp.text()
            async with Browser() as browser:
                await browser.goto(f"{patch_path}.diff")
                patch_file_content = await browser.page.content()
                if patch_file_content.startswith("<html>"):
                    soup = BeautifulSoup(patch_file_content, "html.parser")
                    pre = soup.find("pre")
                    if pre:
                        patch_file_content = pre.text
        else:
            async with aiofiles.open(patch_path, encoding="utf-8") as f:
                patch_file_content = await f.read()
                await EditorReporter().async_report(patch_path)
            if not patch_path.endswith((".diff", ".patch")):
                name = Path(patch_path).name
                patch_file_content = "".join(
                    difflib.unified_diff([], patch_file_content.splitlines(keepends=True), "/dev/null", f"b/{name}"),
                )
                patch_file_content = f"diff --git a/{name} b/{name}\n{patch_file_content}"

        patch: PatchSet = PatchSet(patch_file_content)
        return patch

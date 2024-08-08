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
        cr_output_file: str,
        cr_point_file: Optional[str] = None,
    ) -> str:
        """Review a PR and save code review comments.

        Args:
            patch_path: The local path of the patch file or the url of the pull request. Example: "/data/xxx-pr-1.patch", "https://github.com/xx/XX/pull/1362"
            cr_output_file: Output file path where code review comments will be saved. Example: "cr/xxx-pr-1.json"
            cr_point_file: File path for specifying code review points. If not specified, this parameter is not passed..
        """
        patch = await self._get_patch_content(patch_path)
        cr_point_file = cr_point_file if cr_point_file else Path(metagpt.ext.cr.__file__).parent / "points.json"
        async with aiofiles.open(cr_point_file, "rb") as f:
            cr_point_content = await f.read()
            cr_points = [Point(**i) for i in json.loads(cr_point_content)]

        async with EditorReporter(enable_llm_stream=True) as reporter:
            src_path = cr_output_file
            cr_output_path = Path(cr_output_file)
            await reporter.async_report(
                {"type": "CodeReview", "src_path": src_path, "filename": cr_output_path.name}, "meta"
            )
            comments = await CodeReview_().run(patch, cr_points)
            cr_output_path.parent.mkdir(exist_ok=True, parents=True)
            async with aiofiles.open(cr_output_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(comments, ensure_ascii=False))
            await reporter.async_report(cr_output_path)

        return f"The number of defects: {len(comments)} and the comments are stored in {cr_output_file}"

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

        patch: PatchSet = PatchSet(patch_file_content)
        return patch

import datetime
import itertools
import re
from pathlib import Path
from typing import Optional

from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.ext.cr.utils.cleaner import (
    add_line_num_on_patch,
    get_code_block_from_patch,
    rm_patch_useless_part,
)
from metagpt.utils.common import CodeParser
from metagpt.utils.report import EditorReporter

SYSTEM_MSGS_PROMPT = """
You're an adaptive software developer who excels at refining code based on user inputs. You're proficient in creating Git patches to represent code modifications.
"""

MODIFY_CODE_PROMPT = """
NOTICE
With the given pull-request(PR) Patch, and referenced Comments(Code Standards), you should modify the code according the Comments.

The Patch code has added line no at the first character each line for reading, but the modification should focus on new added code inside the `Patch` (lines starting with line no and '+').

## Patch
```
{patch}
```

## Comments
{comments}

## Output Format
<the standard git patch>


Code Modification guidelines:
- Look at `point_detail`, modify the code by `point_detail`, use `code_start_line` and `code_end_line` to locate the problematic code, fix the problematic code by `point_detail` in Comments.Strictly,must handle the fix plan given by `point_detail` in every comment.
- Create a patch that satifies the git patch standard and your fixes need to be marked with '+' and '-',but notice:don't change the hunk header!
- Do not print line no in the new patch code.

Just print the Patch in the format like **Output Format**.
"""


class ModifyCode(Action):
    name: str = "Modify Code"
    pr: str

    async def run(self, patch: PatchSet, comments: list[dict], output_dir: Optional[str] = None) -> str:
        patch: PatchSet = rm_patch_useless_part(patch)
        patch: PatchSet = add_line_num_on_patch(patch)

        #
        for comment in comments:
            code_start_line = comment.get("code_start_line")
            code_end_line = comment.get("code_end_line")
            # 如果代码位置为空的话，那么就将这条记录丢弃掉
            if code_start_line and code_end_line:
                code = get_code_block_from_patch(
                    patch, str(max(1, int(code_start_line) - 3)), str(int(code_end_line) + 3)
                )
                pattern = r"^[ \t\n\r(){}[\];,]*$"
                if re.match(pattern, code):
                    code = get_code_block_from_patch(
                        patch, str(max(1, int(code_start_line) - 5)), str(int(code_end_line) + 5)
                    )
                # 代码增加上下文，提升代码修复的准确率
                comment["code"] = code
            # 去掉CR时LLM给的comment的影响，应该使用既定的修复方案
            comment.pop("comment")

        # 按照 commented_file 字段进行分组
        comments.sort(key=lambda x: x["commented_file"])
        grouped_comments = {
            key: list(group) for key, group in itertools.groupby(comments, key=lambda x: x["commented_file"])
        }
        resp = None
        for patched_file in patch:
            patch_target_file_name = str(patched_file.path).split("/")[-1]
            if patched_file.path not in grouped_comments:
                continue
            comments_prompt = ""
            index = 1
            for grouped_comment in grouped_comments[patched_file.path]:
                comments_prompt += f"""
                    <comment{index}>
                    {grouped_comment}
                    </comment{index}>\n
                """
                index += 1
            prompt = MODIFY_CODE_PROMPT.format(patch=patched_file, comments=comments_prompt)
            output_dir = (
                Path(output_dir)
                if output_dir
                else self.config.workspace.path / "modify_code" / str(datetime.date.today()) / self.pr
            )
            patch_file = output_dir / f"{patch_target_file_name}.patch"
            patch_file.parent.mkdir(exist_ok=True, parents=True)
            async with EditorReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report(
                    {"type": "Patch", "src_path": str(patch_file), "filename": patch_file.name}, "meta"
                )
                resp = await self.llm.aask(msg=prompt, system_msgs=[SYSTEM_MSGS_PROMPT])
                resp = CodeParser.parse_code(resp, "diff")
                with open(patch_file, "w", encoding="utf-8") as file:
                    file.writelines(resp)
                await reporter.async_report(patch_file)
        return resp

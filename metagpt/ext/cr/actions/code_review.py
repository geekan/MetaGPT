#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import json
import re
from pathlib import Path

import aiofiles
from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.ext.cr.utils.cleaner import (
    add_line_num_on_patch,
    get_code_block_from_patch,
    rm_patch_useless_part,
)
from metagpt.ext.cr.utils.schema import Point
from metagpt.logs import logger
from metagpt.utils.common import parse_json_code_block
from metagpt.utils.report import EditorReporter

CODE_REVIEW_PROMPT_TEMPLATE = """
NOTICE
Let's think and work step by step.
With the given pull-request(PR) Patch, and referenced Points(Code Standards), you should compare each point with the code one-by-one within 4000 tokens.

The Patch code has added line number at the first character each line for reading, but the review should focus on new added code inside the `Patch` (lines starting with line number and '+').
Each point is start with a line number and follows with the point description.

## Patch
```
{patch}
```

## Points
{points}

## Output Format
```json
[
    {{
        "commented_file": "The file path which you give a comment from the patch",
        "comment": "The chinese comment of code which do not meet point description and give modify suggestions",
        "code_start_line": "the code start line number like `10` in the Patch of current comment,",
        "code_end_line": "the code end line number like `15` in the Patch of current comment",
        "point_id": "The point id which the `comment` references to"
    }}
]
```

CodeReview guidelines:
- Generate code `comment` that do not meet the point description.
- Each `comment` should be restricted inside the `commented_file`.
- Try to provide diverse and insightful comments across different `commented_file`.
- Don't suggest to add docstring unless it's necessary indeed.
- If the same code error occurs multiple times, it cannot be omitted, and all places need to be identified.But Don't duplicate at the same place with the same comment!
- Every line of code in the patch needs to be carefully checked, and laziness cannot be omitted. It is necessary to find out all the places.
- The `comment` and `point_id` in the Output must correspond to and belong to the same one `Point`.

Strictly Observe:
Just print the PR Patch comments in json format like **Output Format**.
And the output JSON must be able to be parsed by json.loads() without any errors.
"""

CODE_REVIEW_COMFIRM_SYSTEM_PROMPT = """
You are a professional engineer with {code_language} stack, and good at code review comment result judgement.Let's think and work step by step.
"""

CODE_REVIEW_COMFIRM_TEMPLATE = """
## Code
```
{code}
```
## Code Review Comments
{comment}

## Description of Defects
{desc}

## Reference Example for Judgment
{example}

## Your Task:
1. First, check if the code meets the requirements and does not violate any defects. If it meets the requirements and does not violate any defects, print `False` and do not proceed with further judgment.
2. Based on the `Reference Example for Judgment` provided, determine if the `Code` and `Code Review Comments` match. If they match, print `True`; otherwise, print `False`.

Note: Your output should only be `True` or `False` without any explanations.
"""


class CodeReview(Action):
    name: str = "CodeReview"

    def format_comments(self, comments: list[dict], points: list[Point], patch: PatchSet):
        new_comments = []
        logger.debug(f"original comments: {comments}")
        for cmt in comments:
            try:
                if cmt.get("commented_file").endswith(".py"):
                    points = [p for p in points if p.language == "Python"]
                elif cmt.get("commented_file").endswith(".java"):
                    points = [p for p in points if p.language == "Java"]
                else:
                    continue
                for p in points:
                    point_id = int(cmt.get("point_id", -1))
                    if point_id == p.id:
                        code_start_line = cmt.get("code_start_line")
                        code_end_line = cmt.get("code_end_line")
                        code = get_code_block_from_patch(patch, code_start_line, code_end_line)

                        new_comments.append(
                            {
                                "commented_file": cmt.get("commented_file"),
                                "code": code,
                                "code_start_line": code_start_line,
                                "code_end_line": code_end_line,
                                "comment": cmt.get("comment"),
                                "point_id": p.id,
                                "point": p.text,
                                "point_detail": p.detail,
                            }
                        )
                        break
            except Exception:
                pass

        logger.debug(f"new_comments: {new_comments}")
        return new_comments

    async def confirm_comments(self, patch: PatchSet, comments: list[dict], points: list[Point]) -> list[dict]:
        points_dict = {point.id: point for point in points}
        new_comments = []
        for cmt in comments:
            try:
                point = points_dict[cmt.get("point_id")]

                code_start_line = cmt.get("code_start_line")
                code_end_line = cmt.get("code_end_line")
                # 如果代码位置为空的话，那么就将这条记录丢弃掉
                if not code_start_line or not code_end_line:
                    logger.info("False")
                    continue

                # 代码增加上下文，提升confirm的准确率
                code = get_code_block_from_patch(
                    patch, str(max(1, int(code_start_line) - 3)), str(int(code_end_line) + 3)
                )
                pattern = r"^[ \t\n\r(){}[\];,]*$"
                if re.match(pattern, code):
                    code = get_code_block_from_patch(
                        patch, str(max(1, int(code_start_line) - 5)), str(int(code_end_line) + 5)
                    )
                code_language = "Java"
                code_file_ext = cmt.get("commented_file", ".java").split(".")[-1]
                if code_file_ext == ".java":
                    code_language = "Java"
                elif code_file_ext == ".py":
                    code_language = "Python"
                prompt = CODE_REVIEW_COMFIRM_TEMPLATE.format(
                    code=code,
                    comment=cmt.get("comment"),
                    desc=point.text,
                    example=point.yes_example + "\n" + point.no_example,
                )
                system_prompt = [CODE_REVIEW_COMFIRM_SYSTEM_PROMPT.format(code_language=code_language)]
                resp = await self.llm.aask(prompt, system_msgs=system_prompt)
                if "True" in resp or "true" in resp:
                    new_comments.append(cmt)
            except Exception:
                logger.info("False")
        logger.info(f"original comments num: {len(comments)}, confirmed comments num: {len(new_comments)}")
        return new_comments

    async def cr_by_points(self, patch: PatchSet, points: list[Point]):
        comments = []
        valid_patch_count = 0
        for patched_file in patch:
            if not patched_file:
                continue
            if patched_file.path.endswith(".py"):
                points = [p for p in points if p.language == "Python"]
                valid_patch_count += 1
            elif patched_file.path.endswith(".java"):
                points = [p for p in points if p.language == "Java"]
                valid_patch_count += 1
            else:
                continue
            group_points = [points[i : i + 3] for i in range(0, len(points), 3)]
            for group_point in group_points:
                points_str = "id description\n"
                points_str += "\n".join([f"{p.id} {p.text}" for p in group_point])
                prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(patch=str(patched_file), points=points_str)
                resp = await self.llm.aask(prompt)
                json_str = parse_json_code_block(resp)[0]
                comments_batch = json.loads(json_str)
                if comments_batch:
                    patched_file_path = patched_file.path
                    for c in comments_batch:
                        c["commented_file"] = patched_file_path
                    comments.extend(comments_batch)

        if valid_patch_count == 0:
            raise ValueError("Only code reviews for Python and Java languages are supported.")

        return comments

    async def run(self, patch: PatchSet, points: list[Point], output_file: str):
        patch: PatchSet = rm_patch_useless_part(patch)
        patch: PatchSet = add_line_num_on_patch(patch)

        result = []
        async with EditorReporter(enable_llm_stream=True) as reporter:
            log_cr_output_path = Path(output_file).with_suffix(".log")
            await reporter.async_report(
                {"src_path": str(log_cr_output_path), "filename": log_cr_output_path.name}, "meta"
            )
            comments = await self.cr_by_points(patch=patch, points=points)
            log_cr_output_path.parent.mkdir(exist_ok=True, parents=True)
            async with aiofiles.open(log_cr_output_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(comments, ensure_ascii=False, indent=2))
            await reporter.async_report(log_cr_output_path)

        if len(comments) != 0:
            comments = self.format_comments(comments, points, patch)
            comments = await self.confirm_comments(patch=patch, comments=comments, points=points)
            for comment in comments:
                if comment["code"]:
                    if not (comment["code"].isspace()):
                        result.append(comment)

        async with EditorReporter() as reporter:
            src_path = output_file
            cr_output_path = Path(output_file)
            await reporter.async_report(
                {"type": "CodeReview", "src_path": src_path, "filename": cr_output_path.name}, "meta"
            )
            async with aiofiles.open(cr_output_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(comments, ensure_ascii=False, indent=2))
            await reporter.async_report(cr_output_path)
        return result

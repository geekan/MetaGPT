#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/5/06 13:54
@Author  : wangwenju269
@File    : report.py
"""

import fire

from tests.metagpt.ext.write_report.core_report import ReportRewriter


async def main(auto_run: bool = True):
    requirement = "您的目标是构建一个完整、连贯的事故报告, 请确保您的文字精确、逻辑清晰，并保持专业和客观的写作风格。"
    di = ReportRewriter(auto_run=auto_run, human_design_sop=True, use_evaluator=True)
    await di.run(f"{requirement}", upload_file="<upload file>")


if __name__ == "__main__":
    fire.Fire(main)

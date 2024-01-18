#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_metagpt_oas3_api_svc.py
"""
import asyncio
import subprocess
from pathlib import Path

import pytest
import requests


@pytest.mark.asyncio
async def test_oas2_svc(context):
    workdir = Path(__file__).parent.parent.parent.parent
    script_pathname = workdir / "metagpt/tools/metagpt_oas3_api_svc.py"
    env = context.new_environ()
    env["PYTHONPATH"] = str(workdir) + ":" + env.get("PYTHONPATH", "")
    process = subprocess.Popen(["python", str(script_pathname)], cwd=str(workdir), env=env)
    await asyncio.sleep(5)

    try:
        url = "http://localhost:8080/openapi/greeting/dave"
        headers = {"accept": "text/plain", "Content-Type": "application/json"}
        data = {}
        response = requests.post(url, headers=headers, json=data)
        assert response.text == "Hello dave\n"
    finally:
        process.terminate()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

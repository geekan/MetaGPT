#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_mermaid.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.utils.common import check_cmd_exists
from metagpt.utils.mermaid import MMC1, mermaid_to_file


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ["nodejs", "ink"])  # TODO: playwright and pyppeteer
async def test_mermaid(engine):
    # nodejs prerequisites: npm install -g @mermaid-js/mermaid-cli
    # ink prerequisites: connected to internet
    # playwright prerequisites: playwright install --with-deps chromium
    assert check_cmd_exists("npm") == 0
    assert CONFIG.PYPPETEER_EXECUTABLE_PATH

    CONFIG.mermaid_engine = engine
    save_to = CONFIG.git_repo.workdir / f"{CONFIG.mermaid_engine}/1"
    await mermaid_to_file(MMC1, save_to)

    # ink does not support pdf
    if engine == "ink":
        for ext in [".svg", ".png"]:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)
    else:
        for ext in [".pdf", ".svg", ".png"]:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

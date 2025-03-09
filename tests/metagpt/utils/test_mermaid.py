#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_mermaid.py
"""

import pytest

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.utils.common import check_cmd_exists, new_transaction_id
from metagpt.utils.mermaid import MMC1, mermaid_to_file


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("engine", "suffixes"), [("nodejs", None), ("nodejs", ["png", "svg", "pdf"]), ("ink", None)]
)  # TODO: playwright and pyppeteer
async def test_mermaid(engine, suffixes, context, mermaid_mocker):
    # nodejs prerequisites: npm install -g @mermaid-js/mermaid-cli
    # ink prerequisites: connected to internet
    # playwright prerequisites: playwright install --with-deps chromium
    assert check_cmd_exists("npm") == 0

    save_to = DEFAULT_WORKSPACE_ROOT / f"{new_transaction_id()}/{engine}/1"
    await mermaid_to_file(engine, MMC1, save_to, suffixes=suffixes)

    # ink does not support pdf
    exts = ["." + i for i in suffixes] if suffixes else [".png"]
    if engine == "ink":
        for ext in exts:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)
    else:
        for ext in exts:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

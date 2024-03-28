#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from metagpt.actions.extract_readme import ExtractReadMe
from metagpt.llm import LLM


@pytest.mark.asyncio
async def test_learn_readme(context):
    action = ExtractReadMe(
        name="RedBean",
        i_context=str(Path(__file__).parent.parent.parent.parent),
        llm=LLM(),
        context=context,
    )
    await action.run()
    rows = await action.graph_db.select()
    assert rows
    assert context.repo.docs.graph_repo.changed_files


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

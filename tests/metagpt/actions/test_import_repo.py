#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.actions.import_repo import ImportRepo
from metagpt.context import Context


@pytest.mark.asyncio
@pytest.mark.parametrize("repo_path", ["https://github.com/geekan/MetaGPT.git"])
async def test_import_repo(repo_path):
    context = Context()
    action = ImportRepo(repo_path=repo_path, context=context)
    await action.run()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

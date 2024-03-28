#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.actions.import_repo import ImportRepo
from metagpt.context import Context
from metagpt.utils.common import list_files


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repo_path",
    [
        "https://github.com/spec-first/connexion.git",
        # "https://github.com/geekan/MetaGPT.git"
    ],
)
@pytest.mark.skip
async def test_import_repo(repo_path):
    context = Context()
    action = ImportRepo(repo_path=repo_path, context=context)
    await action.run()
    assert context.repo
    prd = list_files(context.repo.docs.prd.workdir)
    assert prd
    design = list_files(context.repo.docs.system_design.workdir)
    assert design
    assert prd[0].stem == design[0].stem


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

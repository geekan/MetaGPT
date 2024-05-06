#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.context import Context
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import UserMessage
from metagpt.tools.libs.software_development import import_git_repo


@pytest.mark.skip
@pytest.mark.asyncio
async def test_import_repo():
    url = "https://github.com/spec-first/connexion.git"
    path = await import_git_repo(url)
    assert path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        # "create a new issue to github repo 'iorisa/snake-game' :'The snake did not grow longer after eating'",
        "Resolve the issue #1 'Snake not growing longer after eating' in the GitHub repository https://github.com/iorisa/snake-game.git', and create a new pull request about the issue"
    ],
)
async def test_git_create_issue(content: str):
    context = Context()
    di = DataInterpreter(context=context, tools=["<all>"])

    prerequisite = "from metagpt.tools.libs import get_env"
    await di.execute_code.run(code=prerequisite, language="python")
    di.put_message(UserMessage(content=content))
    while not di.is_idle:
        await di.run()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

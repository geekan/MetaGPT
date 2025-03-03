#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Dict

import pytest

from metagpt.tools.libs.software_development import import_git_repo


async def get_env_description() -> Dict[str, str]:
    return {'await get_env(key="access_token", app_name="github")': "get the access token for github authentication."}


@pytest.mark.skip
@pytest.mark.asyncio
async def test_import_repo():
    url = "https://github.com/spec-first/connexion.git"
    path = await import_git_repo(url)
    assert path


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

import pytest
from pydantic import BaseModel

from metagpt.learn.google_search import google_search
from metagpt.tools import SearchEngineType


@pytest.mark.asyncio
async def test_google_search(search_engine_mocker):
    class Input(BaseModel):
        input: str

    inputs = [{"input": "ai agent"}]
    for i in inputs:
        seed = Input(**i)
        result = await google_search(
            seed.input,
            engine=SearchEngineType.SERPER_GOOGLE,
            api_key="mock-serper-key",
        )
        assert result != ""

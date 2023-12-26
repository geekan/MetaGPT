import asyncio

from pydantic import BaseModel

from metagpt.learn.google_search import google_search


async def mock_google_search():
    class Input(BaseModel):
        input: str

    inputs = [{"input": "ai agent"}]

    for i in inputs:
        seed = Input(**i)
        result = await google_search(seed.input)
        assert result != ""


def test_suite():
    loop = asyncio.get_event_loop()
    task = loop.create_task(mock_google_search())
    loop.run_until_complete(task)


if __name__ == "__main__":
    test_suite()

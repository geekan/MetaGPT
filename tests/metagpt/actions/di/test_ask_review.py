import pytest

from metagpt.actions.di.ask_review import AskReview


@pytest.mark.asyncio
async def test_ask_review(mocker):
    mock_review_input = "confirm"
    mocker.patch("metagpt.actions.di.ask_review.get_human_input", return_value=mock_review_input)
    rsp, confirmed = await AskReview().run()
    assert rsp == mock_review_input
    assert confirmed

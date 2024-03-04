import pytest

from metagpt.actions.di.ask_review import AskReview


@pytest.mark.asyncio
async def test_ask_review(mocker):
    mock_review_input = "confirm"
    mocker.patch("builtins.input", return_value=mock_review_input)
    rsp, confirmed = await AskReview().run()
    assert rsp == mock_review_input
    assert confirmed


@pytest.mark.asyncio
async def test_ask_review_llm():
    context = [
        Message("Train a model to predict wine class using the training set."),
        Message(
            """
                       from sklearn.datasets import load_wine
                       wine_data = load_wine()
                       plt.hist(wine_data.target, bins=len(wine_data.target_names))
                       plt.xlabel('Class')
                       plt.ylabel('Number of Samples')
                       plt.title('Distribution of Wine Classes')
                       plt.xticks(range(len(wine_data.target_names)), wine_data.target_names)
                       plt.show()
                       """
        ),
    ]
    rsp, confirmed = await AskReview().run(context, review_type="llm")
    assert rsp.startswith(("redo", "change"))
    assert not confirmed

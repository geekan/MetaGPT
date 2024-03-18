import pytest

from metagpt.actions.di.ask_review import AskReview, ReviewConst
from metagpt.schema import AIMessage, Message


@pytest.mark.asyncio
async def test_ask_review(mocker):
    mock_review_input = "confirm"
    mocker.patch("builtins.input", return_value=mock_review_input)
    rsp, confirmed = await AskReview().run(review_type="human")
    assert rsp == mock_review_input
    assert confirmed


@pytest.mark.asyncio
async def test_ask_review_llm():
    context = [
        Message("task instruction: Train a model to predict wine class using the training set."),
        AIMessage(
            """
            from sklearn.datasets import load_wine
            wine_data = load_wine()
            plt.hist(wine_data.target, bins=len(wine_data.target_names))
            plt.xlabel('Class')
            plt.ylabel('Number of Samples')
            plt.title('Distribution of Wine Classes')
            plt.xticks(range(len(wine_data.target_names)), wine_data.target_names)
            plt.show()
            """.strip()
        ),
    ]
    rsp, confirmed = await AskReview().run(context, review_type="llm")
    assert rsp.startswith(("redo", "change"))
    assert not confirmed


@pytest.fixture()
def unreasonable_plan():
    CONTEXT = """
    ## User Requirement
    "Get paper list that title must include `multiagent` or `large language model` from table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,and save it to a csv file.[I have confirmed the robot protocol, and it is permissible to crawl the website.]"
    ## Context

    ## Current Plan

    ## Current Task

    """
    # 不合理的地方是有很多未知信息需要先探索：1）网页中的哪张表格是论文表；2）论文表的哪个字段是标题；
    unreasonable_plan = """
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Scrape the list of paper titles from the ICLR 2024 statistics page that include 'multiagent' or 'large language model'.",
            "task_type": "web scraping"
        },
        {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Save the scraped list of paper titles to a CSV file.",
            "task_type": "data preprocessing"
        }
    ]
    """
    return [Message(CONTEXT), AIMessage(unreasonable_plan)]


@pytest.fixture()
def reasonable_plan():
    CONTEXT = """
    ## User Requirement
    "Get paper list that title must include `multiagent` or `large language model` from table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,and save it to a csv file.[I have confirmed the robot protocol, and it is permissible to crawl the website.]"
    ## Context

    ## Current Plan

    ## Current Task

    """
    reasonable_plan = """
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Programmatically confirm the robot protocol at https://papercopilot.com/robots.txt, and ensure that scraping the ICLR 2024 statistics page is allowed."
        },
        {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Access the website https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/, parse the web structure using an HTML parser, and locate the specific table with ICLR 2024 paper information."
        },
        {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Confirm the accessibility and structure of the website to ensure proper scraping. Verify that the identified table contains the necessary paper information."
        },
        {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Extract the data from the identified table, ensuring to capture all relevant columns."
        },
        {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Filter the extracted data to include only papers with titles containing `multiagent` or `large language model`, performing a case-insensitive search."
        },
        {
            "task_id": "6",
            "dependent_task_ids": ["5"],
            "instruction": "Define the CSV file structure, including headers for the relevant columns such as title, authors, abstract, and publication date. Specify the format for saving the paper titles."
        },
        {
            "task_id": "7",
            "dependent_task_ids": ["6"],
            "instruction": "Save the filtered data to a CSV file named 'filtered_papers.csv' in a specified directory, and handle any exceptions or errors during the saving process."
        },
        {
            "task_id": "8",
            "dependent_task_ids": ["7"],
            "instruction": "Validate the CSV file to ensure the data is correctly formatted and complete."
        }
    ]
    """
    return [Message(CONTEXT), AIMessage(reasonable_plan)]


@pytest.mark.asyncio
async def test_llm_review_unreasonable_plan(unreasonable_plan):
    rsp, confirmed = await AskReview().run(
        unreasonable_plan, trigger=ReviewConst.PLAN_REVIEW_TRIGGER, review_type="llm"
    )
    print(rsp)
    assert not confirmed
    assert rsp.startswith("change")


@pytest.mark.asyncio
async def test_llm_review_reasonable_plan(reasonable_plan):
    # test reasonable plan
    rsp, confirmed = await AskReview().run(reasonable_plan, trigger=ReviewConst.PLAN_REVIEW_TRIGGER, review_type="llm")
    print(rsp)
    assert confirmed
    assert rsp.startswith("confirm")

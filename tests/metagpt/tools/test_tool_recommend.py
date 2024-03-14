import pytest

from metagpt.schema import Plan, Task
from metagpt.tools import TOOL_REGISTRY
from metagpt.tools.tool_recommend import (
    BM25ToolRecommender,
    ToolRecommender,
    TypeMatchToolRecommender,
)


@pytest.fixture
def mock_plan(mocker):
    task_map = {
        "1": Task(
            task_id="1",
            instruction="conduct feature engineering, add new features on the dataset",
            task_type="feature engineering",
        )
    }
    plan = Plan(
        goal="test requirement",
        tasks=list(task_map.values()),
        task_map=task_map,
        current_task_id="1",
    )
    return plan


@pytest.fixture
def mock_bm25_tr(mocker):
    tr = BM25ToolRecommender(tools=["FillMissingValue", "PolynomialExpansion", "web scraping"])
    return tr


def test_tr_init():
    tr = ToolRecommender(tools=["FillMissingValue", "PolynomialExpansion", "web scraping", "non-existing tool"])
    # web_scraping is a tool tag, it has one tool scrape_web_playwright
    assert list(tr.tools.keys()) == [
        "FillMissingValue",
        "PolynomialExpansion",
        "scrape_web_playwright",
    ]


def test_tr_init_default_tools_value():
    tr = ToolRecommender()
    assert tr.tools == {}


def test_tr_init_tools_all():
    tr = ToolRecommender(tools=["<all>"])
    assert list(tr.tools.keys()) == list(TOOL_REGISTRY.get_all_tools().keys())


@pytest.mark.asyncio
async def test_bm25_tr_recall_with_plan(mock_plan, mock_bm25_tr):
    result = await mock_bm25_tr.recall_tools(plan=mock_plan)
    assert len(result) == 3
    assert result[0].name == "PolynomialExpansion"


@pytest.mark.asyncio
async def test_bm25_tr_recall_no_plan(mock_plan, mock_bm25_tr):
    result = await mock_bm25_tr.recall_tools(
        context="conduct feature engineering, add new features on the dataset", plan=None
    )
    assert len(result) == 3
    assert result[0].name == "PolynomialExpansion"


@pytest.mark.asyncio
async def test_bm25_recommend_tools(mock_bm25_tr):
    result = await mock_bm25_tr.recommend_tools(context="conduct feature engineering, add new features on the dataset")
    assert len(result) == 2  # web scraping tool should be filtered out at rank stage
    assert result[0].name == "PolynomialExpansion"


@pytest.mark.asyncio
async def test_get_recommended_tool_info(mock_plan, mock_bm25_tr):
    result = await mock_bm25_tr.get_recommended_tool_info(plan=mock_plan)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_tm_tr_recall_with_plan(mock_plan, mock_bm25_tr):
    tr = TypeMatchToolRecommender(tools=["FillMissingValue", "PolynomialExpansion", "web scraping"])
    result = await tr.recall_tools(plan=mock_plan)
    assert len(result) == 1
    assert result[0].name == "PolynomialExpansion"

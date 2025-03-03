from unittest.mock import AsyncMock

import pytest

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.logs import logger
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.tools.tool_recommend import BM25ToolRecommender


class TestDataAnalyst:
    def test_init(self):
        analyst = DataAnalyst()
        assert analyst.name == "David"
        assert analyst.profile == "DataAnalyst"
        assert "Browser" in analyst.tools
        assert isinstance(analyst.write_code, WriteAnalysisCode)
        assert isinstance(analyst.execute_code, ExecuteNbCode)

    def test_set_custom_tool(self):
        analyst = DataAnalyst()
        analyst.custom_tools = ["web scraping", "Terminal"]
        assert isinstance(analyst.custom_tool_recommender, BM25ToolRecommender)

    @pytest.mark.asyncio
    async def test_write_and_exec_code_no_task(self):
        analyst = DataAnalyst()
        result = await analyst.write_and_exec_code()
        logger.info(result)
        assert "No current_task found" in result

    @pytest.mark.asyncio
    async def test_write_and_exec_code_success(self):
        analyst = DataAnalyst()
        await analyst.execute_code.init_code()
        analyst.planner.plan.goal = "construct a two-dimensional array"
        analyst.planner.plan.append_task(
            task_id="1",
            dependent_task_ids=[],
            instruction="construct a two-dimensional array",
            assignee="David",
            task_type="DATA_ANALYSIS",
        )

        result = await analyst.write_and_exec_code("construct a two-dimensional array")
        logger.info(result)
        assert "Success" in result

    @pytest.mark.asyncio
    async def test_write_and_exec_code_failure(self):
        analyst = DataAnalyst()
        await analyst.execute_code.init_code()
        analyst.planner.plan.goal = "Execute a code that fails"

        analyst.planner.plan.append_task(
            task_id="1", dependent_task_ids=[], instruction="Execute a code that fails", assignee="David"
        )

        analyst.execute_code.run = AsyncMock(return_value=("Error: Division by zero", False))

        result = await analyst.write_and_exec_code("divide by zero")

        logger.info(result)
        assert "Failed" in result
        assert "Error: Division by zero" in result

    @pytest.mark.asyncio
    async def test_run_special_command(self):
        analyst = DataAnalyst()

        analyst.planner.plan.goal = "test goal"
        analyst.planner.plan.append_task(task_id="1", dependent_task_ids=[], instruction="test task", assignee="David")
        assert not analyst.planner.plan.is_plan_finished()
        cmd = {"command_name": "end"}
        result = await analyst._run_special_command(cmd)
        assert "All tasks are finished" in result
        assert analyst.planner.plan.is_plan_finished()

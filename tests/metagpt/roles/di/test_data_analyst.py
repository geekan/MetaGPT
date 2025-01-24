from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.roles.di.role_zero import RoleZero
from metagpt.strategy.task_type import TaskType
from metagpt.tools.tool_recommend import BM25ToolRecommender


@pytest.fixture
def data_analyst():
    analyst = DataAnalyst()
    analyst.planner = MagicMock()
    analyst.planner.plan = MagicMock()
    analyst.rc = MagicMock()
    analyst.rc.working_memory = MagicMock()
    analyst.rc.memory = MagicMock()
    return analyst


@pytest.fixture
def mock_execute_code():
    with patch('metagpt.actions.di.execute_nb_code.ExecuteNbCode') as mock:
        instance = mock.return_value
        instance.init_code = AsyncMock()
        instance.run = AsyncMock()
        yield instance


@pytest.fixture
def mock_write_code():
    with patch('metagpt.actions.di.write_analysis_code.WriteAnalysisCode') as mock:
        instance = mock.return_value
        instance.run = AsyncMock()
        yield instance


class TestDataAnalyst:
    def test_init(self):
        analyst = DataAnalyst()
        assert analyst.name == "David"
        assert analyst.profile == "DataAnalyst"
        assert "Browser" in analyst.tools
        assert isinstance(analyst.write_code, WriteAnalysisCode)
        assert isinstance(analyst.execute_code, ExecuteNbCode)

    def test_set_custom_tool(self):
        # 测试有自定义工具的情况
        analyst = DataAnalyst()
        analyst.custom_tools = ["web scraping", "Terminal"]
        analyst.custom_tool_recommender = None  # 确保初始值为None
        analyst.set_custom_tool()
        assert isinstance(analyst.custom_tool_recommender, BM25ToolRecommender)

        # 测试没有自定义工具的情况
        analyst = DataAnalyst()
        analyst.custom_tools = []
        analyst.custom_tool_recommender = BM25ToolRecommender(tools=["some_tool"], force=True)  # 设置一个初始值
        analyst.set_custom_tool()
        assert isinstance(analyst.custom_tool_recommender, BM25ToolRecommender)  # 验证即使没有自定义工具，现有的推荐器也保持不变

    @pytest.mark.asyncio
    async def test_write_and_exec_code_no_task(self, data_analyst):
        data_analyst.planner.current_task = None
        result = await data_analyst.write_and_exec_code()
        assert "No current_task found" in result

    @pytest.mark.asyncio
    async def test_write_and_exec_code_success(self, data_analyst, mock_execute_code, mock_write_code):
        # Setup mocks
        data_analyst.planner.current_task = MagicMock()
        data_analyst.planner.get_plan_status.return_value = "Plan status"
        data_analyst.custom_tool_recommender = MagicMock()
        data_analyst.custom_tool_recommender.get_recommended_tool_info = AsyncMock(return_value="Tool info")

        mock_write_code.run.return_value = "test code"
        mock_execute_code.run.return_value = ("Success result", True)

        result = await data_analyst.write_and_exec_code("test instruction")

        assert "Success" in result
        assert mock_execute_code.init_code.called
        assert mock_write_code.run.called
        data_analyst.rc.working_memory.add.assert_called()

    @pytest.mark.asyncio
    async def test_write_and_exec_code_failure(self, data_analyst, mock_execute_code, mock_write_code):
        # Setup mocks
        data_analyst.planner.current_task = MagicMock()
        data_analyst.planner.get_plan_status.return_value = "Plan status"
        data_analyst.custom_tool_recommender = None

        mock_write_code.run.return_value = "test code"
        mock_execute_code.run.return_value = ("Failed result", False)

        result = await data_analyst.write_and_exec_code()

        assert "Failed" in result
        assert mock_execute_code.run.call_count == 3  # Should retry 3 times

    @pytest.mark.asyncio
    async def test_check_data_no_tasks(self, data_analyst):
        data_analyst.planner.plan.get_finished_tasks.return_value = []
        await data_analyst._check_data()
        assert not data_analyst.rc.working_memory.add.called

    @pytest.mark.asyncio
    async def test_check_data_with_data_task(self, data_analyst, mock_execute_code):
        # Setup task with DATA_PREPROCESS type
        task = MagicMock()
        task.task_type = TaskType.DATA_PREPROCESS.type_name
        data_analyst.planner.plan.get_finished_tasks.return_value = [task]
        data_analyst.planner.plan.current_task = task

        with patch('metagpt.actions.di.write_analysis_code.CheckData') as mock_check:
            mock_check.return_value.run = AsyncMock(return_value="check code")
            mock_execute_code.run.return_value = ("check result", True)

            await data_analyst._check_data()

            assert mock_check.return_value.run.called
            assert mock_execute_code.run.called
            data_analyst.rc.working_memory.add.assert_called()

    @pytest.mark.asyncio
    async def test_run_special_command(self, data_analyst):
        data_analyst.planner.plan.is_plan_finished.return_value = False

        cmd = {"command_name": "end"}
        with patch.object(RoleZero, '_run_special_command', return_value="base result"):
            result = await data_analyst._run_special_command(cmd)

        assert "All tasks are finished" in result
        assert data_analyst.planner.plan.finish_all_tasks.called

        # Test non-end command
        cmd = {"command_name": "other"}
        with patch.object(RoleZero, '_run_special_command', return_value="base result"):
            result = await data_analyst._run_special_command(cmd)
        assert result == "base result"

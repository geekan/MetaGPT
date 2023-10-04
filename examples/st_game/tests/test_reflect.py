
import pytest
from examples.st_game.roles.st_role import STRole
from examples.st_game.actions.run_reflect_action import AgentFocusPt
from metagpt.logs import logger


class TestReflectFunction:
    @pytest.fixture
    def init_agent(self):
        # 创建一个STRole实例，注意从GA中copy过来JSON文件
        role = STRole(sim_code="July1_the_ville_isabella_maria_klaus-step-3-11", start_date='February 13, 2023', curr_time='February 13, 2023, 14:53:10')
        logger.info(role.scratch.name)
        logger.info(f"记忆长度为{len(role.memory.storage)}")
        return role

    def test_fuction_point_action(self,init_agent):
        """

        """
        run_focus = AgentFocusPt()
        statements = "" # 这个statements 与 n 设置是遵循reflect里面实际设置# 来的，你写的时候可以对应代码看一下
        run_focus.run(init_agent, statements, n=3)

    # 测试全部Reflection功能
    def test_reflect_function(self, init_agent):
        # 修改 近期 importace 确保Reflect机制能够触发
        init_agent.scratch.importance_trigger_curr = -1
        init_agent.reflect()

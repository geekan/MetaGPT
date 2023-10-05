
import pytest
from examples.st_game.roles.st_role import STRole
from examples.st_game.actions.run_reflect_action import AgentFocusPt, AgentInsightAndGuidance, AgentEventTriple, AgentEventPoignancy, AgentChatPoignancy, AgentPlanThoughtOnConvo, AgentMemoryOnConvo
from metagpt.logs import logger


class TestReflectFunction:
    @pytest.fixture
    def init_agent(self):
        # 创建一个STRole实例，注意从GA中copy过来JSON文件
        role = STRole(sim_code="July1_the_ville_isabella_maria_klaus-step-3-11", start_date='February 13, 2023', curr_time='February 13, 2023, 14:53:10')
        logger.info(role.scratch.name)
        logger.info(f"记忆长度为{len(role.memory.storage)}")
        return role

    def test_function_focus_and_insight_action(self,init_agent):
        """
        单个Action测试样例
        """
        run_focus = AgentFocusPt()
        statements = "" # 这个statements 与 n 设置是遵循reflect里面实际设置# 来的，你写的时候可以对应代码看一下
        run_focus.run(init_agent, statements, n=3)

        run_insight = AgentInsightAndGuidance()
        # 这里主要需要查看，Looger.info(filling)
        # 完善代码

    def test_event_triple_action(self,init_agent):
        """
        测试tripleAgent Action
        """
        pass

    def test_poignancy_action(self,init_agent):
        """
        测试两个关于poignancy的Action
        """
        pass

    def test_convo_action(self,init_agent):
        """
        测试两个convo相关的类
        """
        pass

    # 测试全部Reflection功能
    def test_reflect_function(self, init_agent):
        # 修改 近期 importace 确保Reflect机制能够触发
        init_agent.scratch.importance_trigger_curr = -1
        init_agent.reflect()


import pytest
from examples.st_game.roles.st_role import STRole
from metagpt.logs import logger


class TestReflect:
    @pytest.fixture
    def init_agent(self):
        # 创建一个AgentMemory实例并返回，可以在所有测试用例中共享
        role = STRole('Isabella Rodriguez', 'STMember', 'base_the_vile_isabella_maria_klaus')
        return role

    def test_focus(self, init_agent):
        init_agent.reflect()
"""
测试思路
1. 
"""
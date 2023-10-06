import pytest
from examples.st_game.roles.st_role import STRole
from examples.st_game.actions.run_reflect_action import AgentFocusPt, AgentInsightAndGuidance, AgentEventTriple, \
    AgentEventPoignancy, AgentChatPoignancy, AgentPlanThoughtOnConvo, AgentMemoryOnConvo
from metagpt.logs import logger


class TestReflectFunction:
    @pytest.fixture
    def init_agent(self):
        """
        init STRole form local json, set sim_code(path),curr_time & start_date
        """
        role = STRole(sim_code="July1_the_ville_isabella_maria_klaus-step-3-11", start_date='February 13, 2023',
                      curr_time='February 13, 2023, 14:53:10')
        return role

    def test_function_focus_and_insight_action(self, init_agent):
        """
        test for AgentFocusPt & AgentInsightAndGuidance
        """
        logger.info(f"{__name__}函数启动")
        run_focus = AgentFocusPt()
        statements = ""
        run_focus.run(init_agent, statements, n=3)

        """
        这里有通过测试的结果，但是更多时候LLM生成的结果缺少了because of；考虑修改一下prompt
        result = {'Klaus Mueller and Maria Lopez have a close relationship because they have been friends for a long time and have a strong bond': [1, 2, 5, 9, 11, 14], 'Klaus Mueller has a crush on Maria Lopez': [8, 15, 24], 'Klaus Mueller is academically inclined and actively researching a topic': [13, 20], 'Klaus Mueller is socially active and acquainted with Isabella Rodriguez': [17, 21, 22], 'Klaus Mueller is organized and prepared': [19]}
        """
        run_insight = AgentInsightAndGuidance()
        statements = "[user: Klaus Mueller has a close relationship with Maria Lopez, user:s Mueller and Maria Lopez have a close relationship, user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller and Maria Lopez have a strong relationship, user: Klaus Mueller is a dormmate of Maria Lopez., user: Klaus Mueller and Maria Lopez have a strong bond, user: Klaus Mueller has a crush on Maria Lopez, user: Klaus Mueller and Maria Lopez have been friends for more than 2 years., user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller Maria Lopez is heading off to college., user: Klaus Mueller and Maria Lopez have a close relationship, user: Klaus Mueller is actively researching a topic, user: Klaus Mueller is close friends and classmates with Maria Lopez., user: Klaus Mueller is socially active, user: Klaus Mueller has a crush on Maria Lopez., user: Klaus Mueller and Maria Lopez have been friends for a long time, user: Klaus Mueller is academically inclined, user: For Klaus Mueller's planning: should remember to ask Maria Lopez about her research paper, as she found it interesting that he mentioned it., user: Klaus Mueller is acquainted with Isabella Rodriguez, user: Klaus Mueller is organized and prepared, user: Maria Lopez is conversing about conversing about Maria's research paper mentioned by Klaus, user: Klaus Mueller is conversing about conversing about Maria's research paper mentioned by Klaus, user: Klaus Mueller is a student, user: Klaus Mueller is a student, user: Klaus Mueller is conversing about two friends named Klaus Mueller and Maria Lopez discussing their morning plans and progress on a research paper before Maria heads off to college., user: Klaus Mueller is socially active, user: Klaus Mueller is socially active, user: Klaus Mueller is socially active and acquainted with Isabella Rodriguez, user: Klaus Mueller has a crush on Maria Lopez]"
        run_insight.run(init_agent, statements, n=5)

    def test_event_triple_action(self, init_agent):
        """
        test for AgentEventTriple
        error：遇到复杂情况时（多个Object）无法正确归纳，
        solution: 限制MaxTokens为15
        """
        run_triple = AgentEventTriple()
        statements = "(Klaus Mueller is academically inclined)"
        run_triple.run(statements, init_agent)

    def test_poignancy_action(self, init_agent):
        """
        test for AgentEventPoignancy, AgentChatPoignancy
        done in reflect test
        """
        pass

    def test_convo_action(self, init_agent):
        """
        test for AgentPlanThoughtOnConvo, AgentMemoryOnConvo
        TODO Undone
        """
        pass

    def test_reflect_function(self, init_agent):
        """
        test for reflection
        modify importance_trigger_curr to trigger reflect
        """
        init_agent.scratch.importance_trigger_curr = -1
        init_agent.reflect()

import pytest

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles.di.swe_agent import SWEAgent
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message
from metagpt.tools.libs.terminal import Bash


@pytest.fixture
def env():
    test_env = MGXEnv()
    tl = TeamLeader()
    test_env.add_roles([tl, SWEAgent()])
    return test_env


@pytest.mark.asyncio
async def test_swe_agent(env):
    requirement = "Fix bug in the calculator app"
    swe = env.get_role("Swen")

    message = Message(content=requirement, send_to={swe.name})
    env.publish_message(message)

    await swe.run()

    history = env.history.get()
    agent_messages = [msg for msg in history if msg.sent_from == swe.name]

    assert swe.name == "Swen"
    assert swe.profile == "Issue Solver"
    assert isinstance(swe.terminal, Bash)

    assert "Bash" in swe.tools
    assert "git_create_pull" in swe.tool_execution_map

    def is_valid_instruction_message(msg: Message) -> bool:
        content = msg.content.lower()
        return any(word in content for word in ["git", "bash", "check", "fix"])

    assert any(is_valid_instruction_message(msg) for msg in agent_messages), "Should have valid instruction messages"

from metagpt.actions.action import Action
from metagpt.config2 import Config
from metagpt.const import TEST_DATA_PATH
from metagpt.context import Context
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.roles.role import Role


def test_set_llm():
    config1 = Config.default()
    config2 = Config.default()
    config2.llm.model = "gpt-3.5-turbo"

    context = Context(config=config1)
    act = Action(context=context)
    assert act.config.llm.model == config1.llm.model

    llm2 = create_llm_instance(config2.llm)
    act.llm = llm2
    assert act.llm.model == llm2.model

    role = Role(context=context)
    role.set_actions([act])
    assert act.llm.model == llm2.model

    role1 = Role(context=context)
    act1 = Action(context=context)
    assert act1.config.llm.model == config1.llm.model
    act1.config = config2
    role1.set_actions([act1])
    assert act1.llm.model == llm2.model

    # multiple LLM

    config3_path = TEST_DATA_PATH / "config/config2_multi_llm.yaml"
    dict3 = Config.read_yaml(config3_path)
    config3 = Config(**dict3)
    context3 = Context(config=config3)
    role3 = Role(context=context3)
    act3 = Action(context=context3, llm_name_or_type="YOUR_MODEL_NAME_1")
    assert act3.config.llm.model == "gpt-3.5-turbo"
    assert act3.llm.model == "gpt-4-turbo"
    role3.set_actions([act3])
    assert act3.config.llm.model == "gpt-3.5-turbo"
    assert act3.llm.model == "gpt-4-turbo"

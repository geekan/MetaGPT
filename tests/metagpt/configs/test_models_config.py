import pytest

from metagpt.actions.talk_action import TalkAction
from metagpt.configs.models_config import ModelsConfig
from metagpt.const import METAGPT_ROOT, TEST_DATA_PATH
from metagpt.utils.common import aread, awrite


@pytest.mark.asyncio
async def test_models_configs(context):
    default_model = ModelsConfig.default()
    assert default_model is not None

    models = ModelsConfig.from_yaml_file(TEST_DATA_PATH / "config/config2.yaml")
    assert models

    default_models = ModelsConfig.default()
    backup = ""
    if not default_models.models:
        backup = await aread(filename=METAGPT_ROOT / "config/config2.yaml")
        test_data = await aread(filename=TEST_DATA_PATH / "config/config2.yaml")
        await awrite(filename=METAGPT_ROOT / "config/config2.yaml", data=test_data)

    try:
        action = TalkAction(context=context, i_context="who are you?", llm_name_or_type="YOUR_MODEL_NAME_1")
        assert action.private_llm.config.model == "YOUR_MODEL_NAME_1"
        assert context.config.llm.model != "YOUR_MODEL_NAME_1"
    finally:
        if backup:
            await awrite(filename=METAGPT_ROOT / "config/config2.yaml", data=backup)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

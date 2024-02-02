from pathlib import Path
from random import random
from tempfile import TemporaryDirectory

import pytest

from metagpt.actions.research import CollectLinks
from metagpt.roles import researcher
from metagpt.tools import SearchEngineType
from metagpt.tools.search_engine import SearchEngine


async def mock_llm_ask(self, prompt: str, system_msgs):
    if "Please provide up to 2 necessary keywords" in prompt:
        return '["dataiku", "datarobot"]'
    elif "Provide up to 4 queries related to your research topic" in prompt:
        return (
            '["Dataiku machine learning platform", "DataRobot AI platform comparison", '
            '"Dataiku vs DataRobot features", "Dataiku and DataRobot use cases"]'
        )
    elif "sort the remaining search results" in prompt:
        return "[1,2]"
    elif "Not relevant." in prompt:
        return "Not relevant" if random() > 0.5 else prompt[-100:]
    elif "provide a detailed research report" in prompt:
        return f"# Research Report\n## Introduction\n{prompt}"
    return ""


@pytest.mark.asyncio
async def test_researcher(mocker, search_engine_mocker, context):
    with TemporaryDirectory() as dirname:
        topic = "dataiku vs. datarobot"
        mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
        researcher.RESEARCH_PATH = Path(dirname)
        role = researcher.Researcher(context=context)
        for i in role.actions:
            if isinstance(i, CollectLinks):
                i.search_engine = SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO)
        await role.run(topic)
        assert (researcher.RESEARCH_PATH / f"{topic}.md").read_text().startswith("# Research Report")


def test_write_report(mocker, context):
    with TemporaryDirectory() as dirname:
        for i, topic in enumerate(
            [
                ("1./metagpt"),
                ('2.:"metagpt'),
                ("3.*?<>|metagpt"),
                ("4. metagpt\n"),
            ]
        ):
            researcher.RESEARCH_PATH = Path(dirname)
            content = "# Research Report"
            researcher.Researcher(context=context).write_report(topic, content)
            assert (researcher.RESEARCH_PATH / f"{i+1}. metagpt.md").read_text().startswith("# Research Report")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

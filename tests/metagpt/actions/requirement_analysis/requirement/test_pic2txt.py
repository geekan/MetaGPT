import pytest

from metagpt.actions.requirement_analysis.requirement.pic2txt import Pic2Txt
from metagpt.const import TEST_DATA_PATH
from metagpt.utils.common import aread


@pytest.mark.asyncio
async def test_pic2txt(context):
    images = [
        TEST_DATA_PATH / "requirements/pic/1.png",
        TEST_DATA_PATH / "requirements/pic/2.png",
        TEST_DATA_PATH / "requirements/pic/3.png",
    ]
    textual_user_requirements = await aread(filename=TEST_DATA_PATH / "requirements/1.original_requirement.txt")

    action = Pic2Txt(context=context)
    rsp = await action.run(
        image_paths=images,
        textual_user_requirement=textual_user_requirements,
    )
    assert rsp


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

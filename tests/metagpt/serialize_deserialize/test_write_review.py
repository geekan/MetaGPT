# -*- coding: utf-8 -*-
# @Desc    :
import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_review import WriteReview

TEMPLATE_CONTEXT = """
{
    "Language": "zh_cn",
    "Programming Language": "Python",
    "Original Requirements": "写一个简单的2048",
    "Project Name": "game_2048",
    "Product Goals": [
        "创建一个引人入胜的用户体验",
        "确保高性能",
        "提供可定制的功能"
    ],
    "User Stories": [
        "作为用户，我希望能够选择不同的难度级别",
        "作为玩家，我希望在每局游戏结束后能看到我的得分"
    ],
    "Competitive Analysis": [
        "Python Snake Game: 界面简单，缺乏高级功能"
    ],
    "Competitive Quadrant Chart": "quadrantChart\n    title \"Reach and engagement of campaigns\"\n    x-axis \"Low Reach\" --> \"High Reach\"\n    y-axis \"Low Engagement\" --> \"High Engagement\"\n    quadrant-1 \"我们应该扩展\"\n    quadrant-2 \"需要推广\"\n    quadrant-3 \"重新评估\"\n    quadrant-4 \"可能需要改进\"\n    \"Campaign A\": [0.3, 0.6]\n    \"Campaign B\": [0.45, 0.23]\n    \"Campaign C\": [0.57, 0.69]\n    \"Campaign D\": [0.78, 0.34]\n    \"Campaign E\": [0.40, 0.34]\n    \"Campaign F\": [0.35, 0.78]\n    \"Our Target Product\": [0.5, 0.6]",
    "Requirement Analysis": "产品应该用户友好。",
    "Requirement Pool": [
        [
            "P0",
            "主要代码..."
        ],
        [
            "P0",
            "游戏算法..."
        ]
    ],
    "UI Design draft": "基本功能描述，简单的风格和布局。",
    "Anything UNCLEAR": "..."
}
"""


@pytest.mark.asyncio
async def test_action_serdeser(context):
    action = WriteReview(context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteReview"

    new_action = WriteReview(**serialized_data, context=context)
    review = await new_action.run(TEMPLATE_CONTEXT)

    assert new_action.name == "WriteReview"
    assert type(review) == ActionNode
    assert review.instruct_content
    assert review.get("LGTM") in ["LGTM", "LBTM"]

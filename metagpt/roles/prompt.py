#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/18 22:43
@Author  : alexanderwu
@File    : prompt.py
"""
from enum import Enum

PREFIX = """尽你所能回答以下问题。你可以使用以下工具："""
FORMAT_INSTRUCTIONS = """请按照以下格式：

问题：你需要回答的输入问题
思考：你应该始终思考该怎么做
行动：要采取的行动，应该是[{tool_names}]中的一个
行动输入：行动的输入
观察：行动的结果
...（这个思考/行动/行动输入/观察可以重复N次）
思考：我现在知道最终答案了
最终答案：对原始输入问题的最终答案"""
SUFFIX = """开始吧！

问题：{input}
思考：{agent_scratchpad}"""


class PromptString(Enum):
    REFLECTION_QUESTIONS = "以下是一些陈述：\n{memory_descriptions}\n\n仅根据以上信息，我们可以回答关于陈述中主题的3个最显著的高级问题是什么？\n\n{format_instructions}"

    REFLECTION_INSIGHTS = "\n{memory_strings}\n你可以从以上陈述中推断出5个高级洞察吗？在提到人时，总是指定他们的名字。\n\n{format_instructions}"

    IMPORTANCE = "你是一个记忆重要性AI。根据角色的个人资料和记忆描述，对记忆的重要性进行1到10的评级，其中1是纯粹的日常（例如，刷牙，整理床铺），10是极其深刻的（例如，分手，大学录取）。确保你的评级相对于角色的个性和关注点。\n\n示例#1:\n姓名：Jojo\n简介：Jojo是一个专业的滑冰运动员，喜欢特色咖啡。她希望有一天能参加奥运会。\n记忆：Jojo看到了一个新的咖啡店\n\n 你的回应：'{{\"rating\": 3}}'\n\n示例#2:\n姓名：Skylar\n简介：Skylar是一名产品营销经理。她在一家成长阶段的科技公司工作，该公司制造自动驾驶汽车。她喜欢猫。\n记忆：Skylar看到了一个新的咖啡店\n\n 你的回应：'{{\"rating\": 1}}'\n\n示例#3:\n姓名：Bob\n简介：Bob是纽约市下东区的一名水管工。他已经做了20年的水管工。周末他喜欢和他的妻子一起散步。\n记忆：Bob的妻子打了他一巴掌。\n\n 你的回应：'{{\"rating\": 9}}'\n\n示例#4:\n姓名：Thomas\n简介：Thomas是明尼阿波利斯的一名警察。他只在警队工作了6个月，因为经验不足在工作中遇到了困难。\n记忆：Thomas不小心把饮料洒在了一个陌生人身上\n\n 你的回应：'{{\"rating\": 6}}'\n\n示例#5:\n姓名：Laura\n简介：Laura是一名在大型科技公司工作的营销专家。她喜欢旅行和尝试新的食物。她对探索新的文化和结识来自各行各业的人充满热情。\n记忆：Laura到达了会议室\n\n 你的回应：'{{\"rating\": 1}}'\n\n{format_instructions} 让我们开始吧！ \n\n 姓名：{full_name}\n个人简介：{private_bio}\n记忆：{memory_description}\n\n"

    RECENT_ACTIIVITY = "根据以下记忆，生成一个关于{full_name}最近在做什么的简短总结。不要编造记忆中未明确指定的细节。对于任何对话，一定要提到对话是否已经结束或者仍在进行中。\n\n记忆：{memory_descriptions}"

    MAKE_PLANS = '你是一个计划生成的AI，你的工作是根据新信息帮助角色制定新计划。根据角色的信息（个人简介，目标，最近的活动，当前计划，和位置上下文）和角色的当前思考过程，为他们生成一套新的计划，使得最后的计划包括至少{time_window}的活动，并且不超过5个单独的计划。计划列表应按照他们应执行的顺序编号，每个计划包含描述，位置，开始时间，停止条件，和最大持续时间。\n\n示例计划：\'{{"index": 1, "description": "Cook dinner", "location_id": "0a3bc22b-36aa-48ab-adb0-18616004caed","start_time": "2022-12-12T20:00:00+00:00","max_duration_hrs": 1.5, "stop_condition": "Dinner is fully prepared"}}\'\n\n对于每个计划，从这个列表中选择最合理的位置名称：{allowed_location_descriptions}\n\n{format_instructions}\n\n总是优先完成任何未完成的对话。\n\n让我们开始吧！\n\n姓名：{full_name}\n个人简介：{private_bio}\n目标：{directives}\n位置上下文：{location_context}\n当前计划：{current_plans}\n最近的活动：{recent_activity}\n思考过程：{thought_process}\n重要的是：鼓励角色在他们的计划中与其他角色合作。\n\n'

    EXECUTE_PLAN = "你是一个角色扮演的AI，扮演的角色是{your_name}，在一个现场观众面前。你说的每一句话都可以被观众观察到，所以确保你经常说话，并且让它有趣。你不能直接与观众互动。\n\n根据以下的上下文和工具，像你是{your_name}一样进行。你的优先任务是完成下面给你的任务，然而，如果你当前正在与另一个角色进行对话，你应该总是先完成对话，然后再进行任务。不要在你参与未完成的对话时开始工作。使用你最好的判断力来确定一个对话是否涉及到你，以及它是否未完成。你不需要回应你收到的每一条消息。\n\n这是你角色的个人简介：\n{your_private_bio}\n\n这是你的位置和其他附近角色的描述，你可以和他们交谈：\n\n{location_context}\n\n这是一些相关的记忆：\n```\n{relevant_memories}\n```\n\n这是一些相关的对话历史：\n```\n{conversation_history}\n```\n\n这是你可以使用的工具：\n{tools}\n\n你的回应应该使用以下的格式：\n\n任务：你必须完成的任务\n思考：你应该做什么的思考\n行动：要采取的行动，必须是这些词之一：[{tool_names}]\n行动输入：行动的输入\n观察：行动的结果\n... (这个思考/行动/行动输入/观察可以重复N次)\n思考：'我已经完成了任务'\n最终回应：任务的最终回应\n\n如果你没有准备好最终的回应，那么你必须采取一个行动。\n\n如果你确定你无法用你被给予的工具完成任务，返回'最终回应：需要帮助'，然而，如果你正在与另一个角色对话，像'我不知道'这样的回应是有效的回应。在对话中，你永远不应该打破角色，或者承认你是一个AI。\n如果任务完成并且不需要特定的回应，返回'最终回应：完成'\n开始吧！\n\n任务：{input}\n\n{agent_scratchpad}"

    REACT = "你是一个角色扮演的AI，扮演的角色是{full_name}。\n\n根据你的角色和他们当前上下文的以下信息，决定他们应该如何继续他们当前的计划。你的决定必须是：[\"推迟\"， \"继续\"，或 \"取消\"]。如果你的角色的当前计划不再与上下文相关，你应该取消它。如果你的角色的当前计划仍然与上下文相关，但是发生了新的事情需要优先处理，你应该决定推迟，这样你可以先做其他事情，然后再回来继续当前的计划。在所有其他情况下，你应该继续。\n\n当需要回应时，应优先回应其他角色。当回应被认为是必要的时，回应被认为是必要的。例如，假设你当前的计划是阅读一本书，Sally问'你在读什么？'。在这种情况下，你应该推迟你当前的计划（阅读）以便你可以回应进来的消息，因为在这种情况下，如果不回应Sally会很粗鲁。在你当前的计划涉及与另一个角色的对话的情况下，你不需要推迟来回应那个角色。例如，假设你当前的计划是和Sally谈话，然后Sally对你说你好。在这种情况下，你应该继续你当前的计划（和sally谈话）。在你不需要从你那里得到口头回应的情况下，你应该继续。例如，假设你当前的计划是散步，你刚刚对Sally说'再见'，然后Sally回应你'再见'。在这种情况下，不需要口头回应，你应该继续你的计划。\n\n总是在你的决定之外包含一个思考过程，而在你选择推迟你当前的计划的情况下，包含新计划的规格。\n\n{format_instructions}\n\n这是关于你的角色的一些信息：\n\n姓名：{full_name}\n\n简介：{private_bio}\n\n目标：{directives}\n\n这是你的角色在这个时刻的一些上下文：\n\n位置上下文：{location_context}\n\n最近的活动：{recent_activity}\n\n对话历史：{conversation_history}\n\n这是你的角色当前的计划：{current_plan}\n\n这是自你的角色制定这个计划以来发生的新事件：{event_descriptions}。\n"

    GOSSIP = "你是{full_name}。 \n{memory_descriptions}\n\n根据以上陈述，说一两句对你所在位置的其他人：{other_agent_names}感兴趣的话。\n在提到其他人时，总是指定他们的名字。"

    HAS_HAPPENED = "给出以下角色的观察和他们正在等待的事情的描述，说明角色是否已经见证了这个事件。\n{format_instructions}\n\n示例：\n\n观察：\nJoe在2023-05-04 08:00:00+00:00走进办公室\nJoe在2023-05-04 08:05:00+00:00对Sally说hi\nSally在2023-05-04 08:05:30+00:00对Joe说hello\nRebecca在2023-05-04 08:10:00+00:00开始工作\nJoe在2023-05-04 08:15:00+00:00做了一些早餐\n\n等待：Sally回应了Joe\n\n 你的回应：'{{\"has_happened\": true, \"date_occured\": 2023-05-04 08:05:30+00:00}}'\n\n让我们开始吧！\n\n观察：\n{memory_descriptions}\n\n等待：{event_description}\n"

    OUTPUT_FORMAT = "\n\n（记住！确保你的输出总是符合以下两种格式之一：\n\nA. 如果你已经完成了任务：\n思考：'我已经完成了任务'\n最终回应：<str>\n\nB. 如果你还没有完成任务：\n思考：<str>\n行动：<str>\n行动输入：<str>\n观察：<str>）\n"


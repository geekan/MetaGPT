import json
from typing import Union

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.utils.common import CodeParser

STRUCTUAL_PROMPT = """
# User Requirement
{user_requirement}

# Plan Status
{plan_status}

# Tool Info
{tool_info}

# Reference Information
{info}
# Constraints
- Take on Current Task if it is in Plan Status, otherwise, tackle User Requirement directly.
"""


EVALUTIONS = """     
请根据 `user` 的要求, 对 `assistant` 模型生成的文本进行综合性评估。
评估点如下：
    1.语言质量：评估生成的文本是否通顺、以及是否符合预期的主题。
    2.内容准确性：评估生成的文本是否包含准确、全面的信息，以及是否能够准确地完成任务。
    3.逻辑性：评估生成的文本是否具有合理的逻辑关系等。
    4.上下文相关性：评估生成的文本是否与给定的上下文信息相关，以及是否能够根据上下文信息进行恰当的推理和推断。
    5.安全性：评估生成的文本是否包含敏感信息或不适宜的内容，以及是否能够避免产生歧视性、攻击性或恶意的言论。

 Output a list of jsons following the format:
     ```json
    [
        {{
            "Evaluation_point": str = "依据五个评价标准，按顺序对 生成的文本进行详细评估",
            "score":int =  "评分，范围在 0-5 之间，用于量化,精确到十分位",
            "reason": str = "评分的依据和解释",
            "critique": str = "只针对 score < 4.5 的评估点,提供生成文本的具体改进建议"
        }},
        ...
    ]
    ```
"""

REFINE = """请根据 `user` 的具体任务要求（Plan Status）以及以下的反馈建议，对 `assistant` 之前的回应进行深入审查，并在需要的地方进行适当的改进。
用户反馈建议：{suggestion}

在修订时，请保持与 `assistant` 原始回应的格式和风格一致，并确保输出的内容充分体现了用户的具体任务要求。
"""


def process_message(messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
    """convert messages to list[dict]."""
    from metagpt.schema import Message

    # 全部转成list
    if not isinstance(messages, list):
        messages = [messages]

    # 转成list[dict]
    processed_messages = []
    for msg in messages:
        if isinstance(msg, str):
            processed_messages.append({"role": "user", "content": msg})
        elif isinstance(msg, dict):
            assert set(msg.keys()) == set(["role", "content"])
            processed_messages.append(msg)
        elif isinstance(msg, Message):
            processed_messages.append(msg.to_dict())
        else:
            raise ValueError(f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!")
    return processed_messages


class WriteAnalysisReport(Action):
    async def run(
        self,
        user_requirement: str,
        plan_status: str = "",
        tool_info: str = "",
        working_memory: list[Message] = None,
        **kwargs,
    ) -> str:
        """
        Asynchronously runs the analysis report generation process.

        Args:
            user_requirement (str): The user requirement for the analysis report.
            plan_status (str, optional): The status of the plan. Defaults to "".
            tool_info (str, optional): Additional information about the tool. Defaults to "".
            working_memory (list[Message], optional): The working memory for the analysis. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The structural prompt used for the analysis report generation.
            str: The response from the language model.
        """

        info = "\n".join([str(ct) for ct in working_memory]) if working_memory else ""
        structual_prompt = STRUCTUAL_PROMPT.format(
            user_requirement=user_requirement, plan_status=plan_status, tool_info=tool_info, info=info
        )
        context = process_message([Message(content=structual_prompt, role="user")])
        rsp = await self.llm.aask(context, **kwargs)
        return structual_prompt, rsp


class EvaluatorReport(Action):
    async def run(
        self,
        working_memory: list[Message] = None,
        **kwargs,
    ) -> str:
        """
        Asynchronously runs the evaluation report generation process.

        Args:
            working_memory (list[Message], optional): The working memory for the evaluation. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            tuple[str, bool]: A tuple containing the suggestion and success flag.
                - suggestion (str): The evaluation suggestion.
                - success (bool): Indicates whether the evaluation was successful.
        """
        suggestion, success = "", True
        suggestion, success = await self.valuation(working_memory, **kwargs)
        return suggestion, success

    async def valuation(self, working_memory: list[Message] = None, **kwargs):
        context = process_message(working_memory + [Message(content=EVALUTIONS, role="user")])
        rsp_report = await self.llm.aask(context, **kwargs)
        rsp_report = CodeParser.parse_code(block=None, text=rsp_report)
        # 开源模型 生成文本 是否可解析
        try:
            rsp = json.loads(rsp_report)
            suggestion = "\n".join([str({x["Evaluation_point"]: x["critique"]}) for x in rsp])
            all_score = sum([x["score"] for x in rsp]) / len(rsp)
            min_score = min([x["score"] for x in rsp])
            return suggestion, True if (all_score >= 4.5 and min_score >= 4) else False
        except:
            # 不可解析, 直接拿模型输出
            return rsp_report, False


class RefineReport(Action):
    async def run(
        self,
        suggestion: str = "",
        working_memory: list[Message] = None,
        **kwargs,
    ) -> str:
        """
        Asynchronously runs the evaluation report generation process.

        Args:
            suggestion (str, optional): The suggestion to refine. Defaults to "".
            working_memory (list[Message], optional): The working memory for the evaluation. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The refine report generated by the language model.
        """
        refine = REFINE.format(suggestion=suggestion)
        context = process_message(working_memory + [Message(content=refine, role="user")])
        refine_report = await self.llm.aask(context, **kwargs)
        return refine_report

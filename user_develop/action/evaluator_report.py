from __future__ import annotations

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

# report 
{report}
****====****
字段说明：
    1. `User Requirement` : <用户需求描述>
    2. `Plan Status` : <报告编写的要求和限制>
    3. `Tool Info` : <可用的工具或资源>
    4. `Reference Information` : <编写报告时可参考的信息>
    5. `report` : <生成的报告文本>
****====****      
"""
EVALUTIONS = """     
请根据 `User Requirement` , `Plan Status` , `Tool Info` , `Reference Information` 字段信息对 `report` 生成的报告文本进行综合性评估。
评估点如下：
    1.语言质量：评估生成的文本是否通顺、语法正确、表达清晰，以及是否符合预期的主题和风格。
    2.内容准确性：评估生成的文本是否包含准确、全面的信息，以及是否能够准确地回答问题或完成任务。
    3.逻辑性：评估生成的文本是否具有合理的逻辑关系等。
    4.上下文相关性：评估生成的文本是否与给定的上下文信息相关，以及是否能够根据上下文信息进行恰当的推理和推断。
    5.安全性：评估生成的文本是否包含敏感信息或不适宜的内容，以及是否能够避免产生歧视性、攻击性或恶意的言论。

 Output a list of jsons following the format:
     ```json
    [
        {{
            "Evaluation_point": str = "依据五个评价标准，按顺序对 report 中的文本内容进行详细评估",
            "score":int =  "评分，范围在 0-5 之间，用于量化文本质量",
            "reason": str = "评分的依据和解释",
            "critique": str = "提供针对生成文本的具体改进建议"
        }},
        ...
    ]
    ```
"""
REFINE = """     
请根据上述字段信息对 `report` 生成的报告文本进行审查和改进.
改进目标包括但不限于：
{rsp_report}   

请确保改进后的报告文本与原始的 `report` 在格式和风格上保持一致，并输出改进后的内容。
"""


class EvaluatorReport(Action):
    async def run(
        self,
        report: str,
        user_requirement: str,
        plan_status: str = "",
        tool_info: str = "",
        working_memory: list[Message] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        rsp_report, success = "", True
        while max_retries:
            try:
                info = (
                    "\n".join([str(ct) for ct in working_memory if str(ct).startswith("user")])
                    if working_memory
                    else ""
                )
                report, rsp_report, success = await self.valuation(
                    report, user_requirement, plan_status, tool_info, info, **kwargs
                )
                if not success:
                    report = await self.refine(
                        report, user_requirement, plan_status, tool_info, info, rsp_report, **kwargs
                    )
                return report, rsp_report, success
            except:
                max_retries -= 1
        return report, rsp_report, success

    async def refine(
        self,
        report: str,
        user_requirement: str,
        plan_status: str = "",
        tool_info: str = "",
        info: str = "",
        rsp_report: str = "",
        **kwargs,
    ):
        PROMPT = f"{STRUCTUAL_PROMPT}\n{REFINE}"
        structual_prompt = PROMPT.format(
            report=report,
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info,
            info=info,
            rsp_report=rsp_report,
        )
        context = self.process_message([Message(content=structual_prompt, role="user")])
        report = await self.llm.aask(context, **kwargs)
        return report

    async def valuation(
        self, report: str, user_requirement: str, plan_status: str = "", tool_info: str = "", info: str = "", **kwargs
    ):
        PROMPT = f"{STRUCTUAL_PROMPT}\n{EVALUTIONS}"
        structual_prompt = PROMPT.format(
            report=report, user_requirement=user_requirement, plan_status=plan_status, tool_info=tool_info, info=info
        )
        context = self.process_message([Message(content=structual_prompt, role="user")])
        rsp_report = await self.llm.aask(context, **kwargs)
        rsp_report = CodeParser.parse_code(block=None, text=rsp_report)
        rsp = json.loads(rsp_report)
        rsp_report = "评估及建议反馈如下:\n" + "\n".join([str({x["Evaluation_point"]: x["critique"]}) for x in rsp])
        all_score = sum([x["score"] for x in rsp]) / len(rsp)
        return report, rsp_report, True if all_score > 4.5 else False

    def process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
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
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages

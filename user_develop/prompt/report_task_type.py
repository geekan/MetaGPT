from enum import Enum

from pydantic import BaseModel

from .write_report_paragraph import (
    FIFTH_PROMPT,
    FIRST_PROMPT,
    LAST_PROMPT,
    SECOND_PROMPT,
    SIX_PROMPT,
    THIRD_PROMPT,
)


class TaskTypeDef(BaseModel):
    name: str
    desc: str = ""
    guidance: str = ""


class UserTaskType(Enum):
    """By identifying specific types of tasks, we can inject human priors (guidance) to help task solving"""

    first_paragraph = TaskTypeDef(
        name="first_paragraph", desc="请帮我依据用户所提供事故要点信息进行简要扩写, 完整事故报告的第一自然段。", guidance=FIRST_PROMPT
    )
    second_paragraph = TaskTypeDef(name="second_paragraph", desc="事故发生单位及事发工地概况章节内容", guidance=SECOND_PROMPT)
    third_paragraph = TaskTypeDef(name="third_paragraph", desc="事故发生经过和应急处置情况章节内容", guidance=THIRD_PROMPT)
    forth_paragraph = TaskTypeDef(name="forth_paragraph", desc="事故发生的原因和事故性质章节内容", guidance=FIFTH_PROMPT)
    fifth_paragraph = TaskTypeDef(name="fifth_paragraph", desc="事故责任的认定及处理建议章节内容", guidance=SIX_PROMPT)

    last_paragraph = TaskTypeDef(name="last_paragraph", desc="事故整改及防范措施章节内容", guidance=LAST_PROMPT)

    @property
    def type_name(self):
        return self.value.name

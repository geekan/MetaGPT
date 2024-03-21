from typing import Tuple
from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.utils.common import CodeParser

CSV_PROMPT_TEMPLATE = """
# Context
__context__

-----
You are a professional mathematics assistant.
Please help me validate the above answer using Python code, and Output in Python Block
```python
import os
print('hi')
```end
Attention: Ensure that the output format is bool.
"""


CSV_CONTEXT = """
## User Requirement
{user_requirement}
## Current Answer
{answer}
"""


class CodeSelfVerification(Action):
    
    async def run(self, plan: Plan, answer='', execute_code=None) -> Tuple[str, str, str]:
        context = self.get_context(plan, answer, )
        prompt = CSV_PROMPT_TEMPLATE.replace('__context__', context, )
        llm_res = await self._aask(prompt)
        code = CodeParser().parse_code(block="", text=llm_res)
        result, success = await execute_code.run(code)
        return code, result, success
    
    def get_context(self, plan: Plan, answer: str = "",):
        user_requirement = plan.goal
        context = CSV_CONTEXT.format(user_requirement=user_requirement, answer=answer)
        return context



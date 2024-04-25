import json
from typing import Tuple

from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.utils.common import CodeParser

CODE_REFLECTION_PROMPT_TEMPLATE = """
# Context
__context__

##  Format example
```json
{
    "summary": str = "Make a summary according to the Current Plan, Current Code and Code Runtime Result",
    "status": bool = "Determine whether the the Current Plan is completed correctly",
    "suggestion": str = "If the Current Plan is not completed correctly, provides modification methods and suggestions.Otherwise, an empty string is returned"
    
}
```
-----
You are a world-class programmer, give a summary of the current task.
Output carefully referenced "Format example" in format.
You can make a summary based on the advices below, but you can also add your own analysis.
1.Check that the the Current Plan and Current Code using the right math.
2.Check for any minor miscalculations.
3.Check that the current task using the 'print' function for the output and using fractions/radical forms instead of decimals.
4.Check that the current code result meets the user requirement.
"""

MATH_REVIEW_CONTEXT = """
## User Requirement
{user_requirement}
## Current Plan
{tasks}
## Current Code
{code}
## Code Runtime Result
{result}
"""


class CodeReflection(Action):

    async def run(self, plan: Plan, code='', code_result='',) -> Tuple[str, str, str]:
        context = self.get_context(plan, code, code_result)
        
        cr_prompt = CODE_REFLECTION_PROMPT_TEMPLATE.replace('__context__', context, )
        cr = await self._aask(cr_prompt)
        cr = CodeParser.parse_code(block=None, text=cr)
        try:
            cr = json.loads(cr)
        except:
            cr = cr.replace('\\', '\\\\')
            cr = json.loads(cr)
        
        summary = ''
        status = False
        suggestion = ''
        if 'status' in cr and 'summary' in cr and 'suggestion' in cr:
            summary = cr['summary']
            status = cr['status']
            suggestion = cr['suggestion']
        
        return summary, status, suggestion
    
    def get_context(self, plan: Plan, code: str = "", runtime_result: str = ""):
        user_requirement = plan.goal

        def process_task(task):
            ptask = f"{task.task_id}:{task.instruction}"
            return ptask
        
        tasks = json.dumps([process_task(task) for task in plan.tasks], indent=4, ensure_ascii=False)
        context = MATH_REVIEW_CONTEXT.format(
            user_requirement=user_requirement, tasks=tasks, code=code, result=runtime_result
        )
        return context


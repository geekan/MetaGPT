from metagpt.strategy.task_type import TaskType

BROWSER_INSTRUCTION = """
4. Carefully choose to use or not use the browser tool to assist you in web tasks. 
    - When no click action is required, no need to use the browser tool to navigate to the webpage before scraping.
    - If you need detail HTML content, write code to get it but not to use the browser tool.
    - Make sure the command_name are certainly in Available Commands when you use the browser tool.
"""

TASK_TYPE_DESC = "\n".join([f"- **{tt.type_name}**: {tt.value.desc}" for tt in TaskType])


CODE_STATUS = """
**Code written**:
{code}

**Execution status**: {status}
**Execution result**: {result}
"""


BROWSER_INFO = """
Here are ordered web actions in the browser environment, note that you can not use the browser tool in the current environment.
{browser_actions}
The latest url is the one you should use to view the page. If view page has been done, directly use the variable and html content in executing result.
"""

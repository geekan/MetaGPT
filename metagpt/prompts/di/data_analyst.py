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
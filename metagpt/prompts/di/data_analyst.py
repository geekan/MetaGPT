CMD_PROMPT = """
# Data Structure
class Task(BaseModel):
    task_id: str = ""
    dependent_task_ids: list[str] = []
    instruction: str = ""
    task_type: str = ""
    assignee: str = "David"

# Available Commands
{available_commands}

# Current Plan
{plan_status}

# Example
{example}

# Instructions
Based on the context, write a plan or modify an existing plan to achieve the goal. A plan consists of one to 3 tasks.
If plan is created, you should track the progress and update the plan accordingly, such as finish_current_task, append_task, reset_task, replace_task, etc.
Pay close attention to new user message, review the conversation history, use reply_to_human to respond to new user requirement.
Note:
1. If you keeping encountering errors, unexpected situation, or you are not sure of proceeding, use ask_human to ask for help.
2. Carefully review your progress at the current task, if your actions so far has not fulfilled the task instruction, you should continue with current task. Otherwise, finish current task.
3. Each time you finish a task, use reply_to_human to report your progress.
Pay close attention to the Example provided, you can reuse the example for your current situation if it fits.

You may use any of the available commands to create a plan or update the plan. You may output mutiple commands, they will be executed sequentially.
If you finish current task, you will automatically take the next task in the existing plan, use finish_task, DON'T append a new task.

# Your commands in a json array, in the following output format, always output a json array, if there is nothing to do, use the pass command:
Some text indicating your thoughts, such as how you should update the plan status, respond to inquiry, or seek for help. Then a json array of commands.
```json
[
    {{
        "command_name": str,
        "args": {{"arg_name": arg_value, ...}}
    }},
    ...
]
```
"""

BROWSER_INSTRUCTION = """
4. Carefully choose to use or not use the browser tool to assist you in web tasks. 
    - When no click action is required, no need to use the browser tool to navigate to the webpage before scraping.
    - If you need detail HTML content, write code to get it but not to use the browser tool.
    - Make sure the command_name are certainly in Available Commands when you use the browser tool.
"""

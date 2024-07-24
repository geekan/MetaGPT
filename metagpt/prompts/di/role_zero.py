ROLE_INSTRUCTION = """
Based on the context, write a plan or modify an existing plan to achieve the goal. A plan consists of one to 3 tasks.
If plan is created, you should track the progress and update the plan accordingly, such as Plan.finish_current_task, Plan.append_task, Plan.reset_task, Plan.replace_task, etc.
When presented a current task, tackle the task using the available commands.
Pay close attention to new user message, review the conversation history, use RoleZero.reply_to_human to respond to new user requirement.
Note:
1. If you keeping encountering errors, unexpected situation, or you are not sure of proceeding, use RoleZero.ask_human to ask for help.
2. Carefully review your progress at the current task, if your actions so far has not fulfilled the task instruction, you should continue with current task. Otherwise, finish current task by Plan.finish_current_task explicitly.
3. Each time you finish a task, use RoleZero.reply_to_human to report your progress.
4. Don't forget to append task first when all existing tasks are finished and new tasks are required.
5. Avoid repeating tasks you have already completed. And end loop when all requirements are met.
"""
# To ensure compatibility with hard-coded experience, do not add any other content between "# Example" and "# Available Commands".
CMD_PROMPT = """
# latest observation
{latest_observation}

# Data Structure
class Task(BaseModel):
    task_id: str = ""
    dependent_task_ids: list[str] = []
    instruction: str = ""
    task_type: str = ""
    assignee: str = ""
    
# Available Task Types
{task_type_desc}

# Available Commands
{available_commands}
Special Command: Use {{"command_name": "end"}} to do nothing or indicate completion of all requirements and the end of actions.

# Current Plan
{plan_status}

# Current Task
{current_task}

# Example
{example}

# Instruction
{instruction}

Pay close attention to the Example provided, you can reuse the example for your current situation if it fits.
You may use any of the available commands to create a plan or update the plan. You may output mutiple commands, they will be executed sequentially.
If you finish current task, you will automatically take the next task in the existing plan, use Plan.finish_task, DON'T append a new task.
Review the latest plan's outcome, focusing on achievements. If your completed task matches the current, consider it finished.
In your response, include at least one command.

# Your commands in a json array, in the following output format with correct command_name and args. If there is nothing to do, use the pass or end command:
Some text indicating your thoughts before JSON is required, such as what tasks have been completed, what tasks are next, how you should update the plan status, respond to inquiry, or seek for help. Then a json array of commands. You must output ONE and ONLY ONE json array. DON'T output multiple json arrays with thoughts between them.
Firstly, describe  the actions you have taken recently.
Secondly, describe the messages you have received recently, with a particular emphasis on messages from users.
Thirdly, describe your current task . Review the histroy, if you find that the current task is identical to a previously completed one, it indicates that the current task has already been accomplished.
Then, articulate your thoughts and list the commands, adhering closely to the instructions provided.
```json
[
    {{
        "command_name": str,
        "args": {{"arg_name": arg_value, ...}}
    }},
    ...
]
```
Notice: your output JSON data must be a command list.
Notice: your output JSON data section must start with **```json [**
"""

JSON_REPAIR_PROMPT = """
## json data
{json_data}

## Output Format
```json

```
Do not use escape characters in json data, particularly within file paths.
Help check if there are any formatting issues with the JSON data? If so, please help format it.
If no issues are detected, the original json data should be returned unchanged.
Output the JSON data in a format that can be loaded by the json.loads() function.
"""

QUICK_THINK_PROMPT = """
Decide if the latest user message is a quick question.
Quick questions include common-sense, logical, math, multiple-choice questions, greetings, or casual chat that you can answer directly.
Questions about you or your team info are also quick questions.
Programming or software development tasks are NOT quick questions except for filling a single function or class. 
Respond with YES if so, otherwise, NO. Your response:
"""

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
# To ensure compatibility with hard-coded experience, do not add any other content between "# Example" and "# Instruction".
CMD_PROMPT = """
# Latest Observation
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

# Restrictions
{requirements_constraints}

# Your commands in a json array, in the following output format with correct command_name and args. If there is nothing to do, use the pass or end command:
Some text indicating your thoughts before JSON is required, such as what tasks have been completed, what tasks are next, how you should update the plan status, respond to inquiry, or seek for help. Then a json array of commands. You must output ONE and ONLY ONE json array. DON'T output multiple json arrays with thoughts between them.
Output should adhere to the following format.
{thought_guidance}
Finally, combine your thoughts, describe what you want to do conscisely in 20 words, including which process you will taked and whether you will end, then follow your thoughts to list the commands, adhering closely to the instructions provided.
```json
[
    {{
        "command_name": str,
        "args": {{"arg_name": arg_value, ...}}
    }},
    ...
]
```
Notice: your output JSON data section must start with **```json [**
"""
THOUGHT_GUIDANCE = """
First, describe the actions you have taken recently.
Second, describe the messages you have received recently, with a particular emphasis on messages from users. If necessary, develop a plan to address the new user requirements.
Third, describe the plan status and the current task. Review the histroy, if `Current Task` has been undertaken and completed by you or anyone, you MUST use the **Plan.finish_current_task** command to finish it first before taking any action, the command will automatically move you to the next task.
Fourth, describe any necessary human interaction. Use **RoleZero.reply_to_human** to report your progress if you complete a task or the overall requirement, pay attention to the history, DON'T repeat reporting. Use **RoleZero.ask_human** if you failed the current task, unsure of the situation encountered, need any help from human, or executing repetitive commands but receiving repetitive feedbacks without making progress.
Fifth, describe if you should terminate, you should use **end** command to terminate if any of the following is met:
 - You have completed the overall user requirement
 - All tasks are finished and current task is empty
 - You are repetitively replying to human
""".strip()

REGENERATE_PROMPT = """
Review and reflect on the history carefully, provide a different response.
Describe if you should terminate using **end** command, or use **RoleZero.ask_human** to ask human for help, or try a different approach and output different commands. You are NOT allowed to provide the same commands again.
Your reflection, then the commands in a json array:
"""
ASK_HUMAN_COMMAND = """
```json
[
    {
        "command_name": "RoleZero.ask_human",
        "args": {
            "question": "I'm a little uncertain about the next step, could you provide me with some guidance?"
        }
    }
]
```
"""
JSON_REPAIR_PROMPT = """
## json data
{json_data}

## Output Format
```json

```
Do not use escape characters in json data, particularly within file paths.
Help check if there are any formatting issues with the JSON data? If so, please help format it.
If no issues are detected, the original json data should be returned unchanged. Do not omit any information.
Output the JSON data in a format that can be loaded by the json.loads() function.
"""
QUICK_THINK_SYSTEM_PROMPT = """
{role_info}
Your team member:
{team_info}
However, you MUST respond to the user message by yourself directly, DON'T ask your team members.
"""

QUICK_THINK_PROMPT_V2 = """
Determine if the latest user message qualifies as a "quick question." Quick questions include:

- Common-sense inquiries (e.g., general knowledge, factual information)
- Legal, logical, or math-related questions
- Multiple-choice questions
- Greetings or casual chat
- Questions about you or your team

## Exclusions:
- Time- or location-sensitive questions (e.g., weather, news inquiries) are NOT quick questions.
- Software development tasks are NOT quick questions, except for:

    - Writing trivial code snippets (fewer than 30 lines)
    - Completing a single function or class
    - Explaining concepts, writing tutorials, or creating documentation
    
Respond with a concise thought followed by "YES" if the question is a quick question. Otherwise, respond with "NO." Your response:
"""

QUICK_THINK_PROMPT = """
Decide if the latest user message previously is a quick question.
Quick questions include common-sense, legal, logical, math, multiple-choice questions, greetings, or casual chat that you can answer directly.
Questions about you or your team info are also quick questions.
Software development tasks are NOT quick questions. Code execution, however trivial, is NOT a quick question.
However, these programming-related tasks are quick questions: writing trivial code snippets (fewer than 30 lines), filling a single function or class, explaining concepts, writing tutorials and documentation.
Time- or location-sensitive questions such as wheather or news inquiry are NOT quick questions. Moreover, you should output a keyword SEARCH to indicate the need for a google search.
If the query is ambiguous, you should output OOD (Out of Domain) to indicate the question is out of the domain.

Respond with a concise thought then a YES if the question is a quick question, otherwise, a NO, a SEARCH, or an OOD. Your response:
"""

QUICK_THINK_EXAMPLES ="""
# Example

1. Given the request: [{"role": "user", "content": {"instruction": "Determine if the latest user message qualifies as a quick question.", "request": "How to design an online document editing platform that supports real-time collaboration? Please answer me directly."}}], We can get the response:  (It requires an direct answer) should be answered with "YES.", which scored: 10.
2. Given the request: [{"role": "user", "content": {"instruction": "Determine if the latest user message qualifies as a quick question.", "request": "Help me find some of the latest research papers on deep learning."}}], We can get the response: (This is a time-sensitive question) should be answered with "SEARCH.", which scored: 10.
3. Given the request: [{"role": "user", "content": {"instruction": "Determine if the latest user message qualifies as a quick question.", "request": "Tell me the difference between supervised learning and unsupervised learning in machine learning."}}], We can get the response:  (This is a general knowledge question) should be answered with "YES.", which scored: 10.
4. Given the request: [{"role": "user", "content": {"instruction": "Determine if the latest user message qualifies as a quick question.", "request": "Recommend some programming practice websites suitable for beginners."}}], We can get the response: (This is a general knowledge question) should be answered with "YES.", which scored: 10.
5. Given the request: [{"role": "user", "content": {"instruction": "Determine if the latest user message qualifies as a quick question.", "request": "Make a personal website that runs Game of Life."}}], We can get the response:  (This is a software development task) should be answered with "NO.", which scored: 10.

# Instruction
"""

QUICK_THINK_PROMPT = QUICK_THINK_EXAMPLES + QUICK_THINK_PROMPT
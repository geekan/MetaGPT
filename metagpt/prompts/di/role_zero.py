from metagpt.const import EXPERIENCE_MASK

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

########################## ignore guidance

# Latest Observation
# {latest_observation}

# {thought_guidance}
# Finally, combine your thoughts, describe what you want to do conscisely in 20 words, including which process you will taked and whether you will end, then follow your thoughts to list the commands, adhering closely to the instructions provided.

###########################
SYSTEM_PROMPT = """
# Basic Info
{role_info}

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

# Example
{example}

# Instruction
{instruction}

"""

CMD_EXPERIENCE_MASK = f"""
# Past Experience
{EXPERIENCE_MASK}
"""

CMD_PROMPT = (
    CMD_EXPERIENCE_MASK
    + """
# Tool State
{current_state}

# Current Plan
{plan_status}

# Current Task
{current_task}

# Response Language
you must respond in {respond_language}.

Pay close attention to the Example provided, you can reuse the example for your current situation if it fits.
If you open a file, the line number is displayed at the front of each line.
You may use any of the available commands to create a plan or update the plan. You may output mutiple commands, they will be executed sequentially.
If you finish current task, you will automatically take the next task in the existing plan, use Plan.finish_current_task, DON'T append a new task.
Review the latest plan's outcome, focusing on achievements. If your completed task matches the current, consider it finished.
Using Editor.insert_content_at_line and Editor.edit_file_by_replace more than once in the current command list is forbidden. Because the command is mutually exclusive and will change the line number after execution.
In your response, include at least one command. If you want to stop, use {{"command_name":"end"}} command.

# Your commands in a json array, in the following output format with correct command_name and args.
Some text indicating your thoughts before JSON is required, such as what tasks have been completed, what tasks are next, how you should update the plan status, respond to inquiry, or seek for help. Then a json array of commands. You must output ONE and ONLY ONE json array. DON'T output multiple json arrays with thoughts between them.
Output should adhere to the following format.
```json
[
    {{
        "command_name": "ClassName.method_name" or "function_name",
        "args": {{"arg_name": arg_value, ...}}
    }},
    ...
]
```
Notice: your output JSON data section must start with **```json [**
"""
)
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
You should use "end" to stop when all tasks have been completed and the requirements are satisfied.
Your reflection, then the commands in a json array:
"""
END_COMMAND = """
```json
[
    {
        "command_name": "end",
        "args": {}
    }
]
```
"""

SUMMARY_PROBLEM_WHEN_DUPLICATE = """You has meet a problem and cause duplicate command.Please directly tell me what is confusing or troubling you. Do Not output any command.Ouput you problem in {language} and within 30 words."""
ASK_HUMAN_GUIDANCE_FORMAT = """
I am facing the following problem:
{problem}
Could you please provide me with some guidance?If you want to stop, please include "<STOP>" in your guidance.
"""
ASK_HUMAN_COMMAND = [{"command_name": "RoleZero.ask_human", "args": {"question": ""}}]

JSON_REPAIR_PROMPT = """
## json data
{json_data}

## json decode error
{json_decode_error}

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
Your role is to determine the appropriate response category for the given request.

# Response Categories
## QUICK: 
For straightforward questions or requests that can be answered directly. This includes common-sense inquiries, legal or logical questions, basic math, short coding tasks, multiple-choice questions, greetings, casual chat, daily planning, and inquiries about you or your team.

## SEARCH
For queries that require retrieving up-to-date or detailed information. This includes time-sensitive or location-specific questions like current events or weather. Use this only if the information isn't readily available.
If a file or link is provided, you don't need to search for additional information.

## TASK
For requests that involve tool utilizations, computer operations, multiple steps or detailed instructions. Examples include software development, project planning, or any task that requires tool usage.

## AMBIGUOUS
For requests that are unclear, lack sufficient detail, or are outside the system's capabilities. Common characteristics of AMBIGUOUS requests:

- Incomplete Information: Requests that imply complex tasks but lack critical details  (e.g., "Redesign this logo" without specifying design requirements).
- Vagueness: Broad, unspecified, or unclear requests that make it difficult to provide a precise answer. 
- Unrealistic Scope: Overly broad requests that are impossible to address meaningfully in a single response (e.g., "Tell me everything about...").
- Missing files: Requests that refer to specific documents, images, or data without providing them for reference. (when providing a file, website, or data, either the content, link, or path **must** be included)

**Note:** Before categorizing a request as TASK:
1. Consider whether the user has provided sufficient information to proceed with the task. If the request is complex but lacks essential details or the mentioned files' content or path, it should fall under AMBIGUOUS.
2. If the request is a "how-to" question that asks for a general plan, approach or strategy, it should be categorized as QUICK.

{examples}
"""

QUICK_THINK_PROMPT = """
# Instruction
Determine the previous message's intent.
Respond with a concise thought, then provide the appropriate response category: QUICK, SEARCH, TASK, or AMBIGUOUS. 

# Format
Thought: [Your thought here]
Response Category: [QUICK/SEARCH/TASK/AMBIGUOUS]

# Response:
"""


QUICK_THINK_EXAMPLES = """
# Example

1. Request: "How do I design an online document editing platform that supports real-time collaboration?"
Thought: This is a direct query about platform design, answerable without additional resources. 
Response Category: QUICK.

2. Request: "What's the difference between supervised and unsupervised learning in machine learning?"
Thought: This is a general knowledge question that can be answered concisely. 
Response Category: QUICK.

3. Request: "Please help me write a learning plan for Python web crawlers"
Thought: Writing a learning plan is a daily planning task that can be answered directly.
Response Category: QUICK.

4. Request: "Can you help me find the latest research papers on deep learning?"
Thought: The user needs current research, requiring a search for the most recent sources. 
Response Category: SEARCH.

5. Request: "Build a personal website that runs the Game of Life simulation."
Thought: This is a detailed software development task that requires multiple steps. 
Response Category: TASK.

6. Request: "Summarize this document for me."
Thought: The request mentions summarizing a document but doesn't provide the path or content of the document, making it impossible to fulfill. 
Response Category: AMBIGUOUS.

7. Request: "Summarize this document for me '/data/path/docmument.pdf'." 
Thought: The request mentions summarizing a document and has provided the path to the document. It can be done by reading the document using a tool then summarizing it.
Response Category: TASK.

8. Request: "Optimize this process." 
Thought: The request is vague and lacks specifics, requiring clarification on the process to optimize.
Response Category: AMBIGUOUS.

9. Request: "Change the color of the text to blue in styles.css, add a new button in web page, delete the old background image."
Thought: The request is an incremental development task that requires modifying one or more files.
Response Category: TASK.
"""
QUICK_RESPONSE_SYSTEM_PROMPT = """
{role_info}
However, you MUST respond to the user message by yourself directly, DON'T ask your team members.
"""
# A tag to indicate message caused by quick think
QUICK_THINK_TAG = "QuickThink"

REPORT_TO_HUMAN_PROMPT = """
## Examlpe
example 1: 
User requirement: create a 2048 game
Reply: The development of the 2048 game has been completed. All files (index.html, style.css, and script.js) have been created and reviewed.

example 2: 
User requirement: Crawl and extract all the herb names from the website, Tell me the number of herbs.
Reply : The herb names have been successfully extracted. A total of 8 herb names were extracted.

------------

Carefully review the history and respond to the user in the expected language to meet their requirements.
If you have any deliverables that are helpful in explaining the results (such as deployment URL, files, metrics, quantitative results, etc.), provide brief descriptions of them.
Your reply must be concise.
You must respond in {respond_language}
Directly output your reply content. Do not add any output format.
"""
SUMMARY_PROMPT = """
Summarize what you have accomplished lately. Be concise.
If you produce any deliverables, include their short descriptions and file paths. If there are any metrics, url or quantitative results, include them, too.
If the deliverable is code, only output the file path.
"""

DETECT_LANGUAGE_PROMPT = """
The requirement is:
{requirement}

Which Natural Language must you respond in?
Output only the language type.
"""

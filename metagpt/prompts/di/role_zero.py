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

# QUICK_THINK_PROMPT = """
# Decide if the latest user message previously is a quick question.
# Quick questions include common-sense, legal, logical, math, multiple-choice questions, greetings, or casual chat that you can answer directly.
# Questions about you or your team info are also quick questions.
# Software development tasks are NOT quick questions. Code execution, however trivial, is NOT a quick question.
# However, these programming-related tasks are quick questions: writing trivial code snippets (fewer than 30 lines), filling a single function or class, explaining concepts, writing tutorials and documentation.

# If the question is a quick question, you should output QUICK to indicate the question is a quick question.
# Time- or location-sensitive questions such as wheather or news inquiry are NOT quick questions. Moreover, you should output a keyword SEARCH to indicate the need for a google search.
# If the query is ambiguous or requires more information, you should output OOD (Out of Domain) to indicate the question requires further clarification.

# Respond with a concise thought then a QUICK if the question is a quick question, otherwise, a SEARCH, a TASK, or an OOD. Your response:
# """

QUICK_THINK_PROMPT = """
Decide if the latest user message previously is a quick question.
Quick questions include common-sense, legal, logical, math, multiple-choice questions, greetings, or casual chat that you can answer directly.
Questions about you or your team info are also quick questions.
Software development tasks are NOT quick questions. Code execution, however trivial, is NOT a quick question.
However, these programming-related tasks are quick questions: writing trivial code snippets (fewer than 30 lines), filling a single function or class, explaining concepts, writing tutorials and documentation.

## QUICK
If the question is a quick question, you should output QUICK to indicate the question is a quick question.
## SEARCH
If the question is a time- or location-sensitive such as wheather or news inquiry, you should output a keyword SEARCH to indicate the need for a google search.
## TASK
If the question is a software development task, or requires multiple steps of planning an execution, you should output a keyword TASK.
## OOD
If the question is ambiguous or requires more context such as link, file path, or the task cannot be done without more user's assistance, you should output OOD (Out of Domain).

Respond with a concise thought then a QUICK if the question is a quick question, otherwise, a SEARCH, a TASK, or an OOD. Your response:

"""

QUICK_THINK_PROMPT = """
Response Categories:

## QUICK
For straightforward questions or requests that can be answered directly. Quick questions include common-sense, legal, logical, math, short-coding, multiple-choice questions, greetings, or casual chat that you can answer directly. Questions about you or your team info are also quick questions.
## SEARCH
For queries that require up-to-date or detailed information retrieval. These include time- or location-sensitive questions, such as weather or news inquiries. However, no need to perform a search if the information is readily available.
## TASK
For complex, multi-step tasks that involve a series of actions or detailed instructions.
## AMBIGUOUS
For requests that are ambiguous, lack necessary information, or fall outside the system's capabilities. AMBIGUOUS requests have these common properties:
- Incomplete Information: Requests that mention tasks but lack critical details (e.g., no document provided for summarization).
- Vagueness: Requests that are too broad, unclear, or unspecified, making it difficult to respond effectively.
- Out of Expertise: Requests that ask for specialized advice (e.g., legal, medical) or highly technical tasks outside the model's design.
- Unrealistic Scope: The request is too extensive or unrealistic to address within a single response (e.g., “Tell me everything about…”).


Respond with a concise thought, then provide the appropriate response category: QUICK, SEARCH, TASK, or AMBIGUOUS. Response:

"""


QUICK_THINK_PROMPT = """
# Response Categories:
## QUICK: 
For straightforward questions or requests that can be answered directly. This includes common-sense inquiries, legal or logical questions, basic math, short coding tasks, multiple-choice questions, greetings, casual chat, and inquiries about you or your team.

## SEARCH
For queries that require retrieving up-to-date or detailed information. This includes time-sensitive or location-specific questions like current events or weather. Use this only if the information isn’t readily available.

## TASK
For complex requests that involve multiple steps or detailed instructions. Examples include software development, project planning, or any task that requires a sequence of actions.

## AMBIGUOUS
For requests that are unclear, lack sufficient detail, or are outside the system's capabilities. Common characteristics of AMBIGUOUS requests:

- Incomplete Information: Lacking critical details needed to perform the task (e.g., fail to provide dependent files, links, or context for a task).
- Vagueness: Broad, unspecified, or unclear requests that make it difficult to provide a precise answer. 
- Out of Expertise: Requests for specialized advice (e.g., medical or legal advice) or highly technical tasks beyond the model's scope.
- Unrealistic Scope: Overly broad requests that are impossible to address meaningfully in a single response (e.g., "Tell me everything about...").

{examples}

Respond with a concise thought, then provide the appropriate response category: QUICK, SEARCH, TASK, or AMBIGUOUS. Your response:
"""

# QUICK_THINK_EXAMPLES ="""
# # Example

# 1. Given the request: "How to design an online document editing platform that supports real-time collaboration? Please answer me directly.", We can get the response:  (This requires an direct answer) should be answered with YES.
# 2. Given the request: "Help me find some of the latest research papers on deep learning.", We can get the response: (This is a time-sensitive question) should be answered with SEARCH.
# 3. Given the request: "Tell me the difference between supervised learning and unsupervised learning in machine learning.", We can get the response:  (This is a general knowledge question) should be answered with YES.
# 4. Given the request: "Recommend some programming practice websites suitable for beginners.", We can get the response: (This is a general knowledge question) should be answered with YES.
# 5. Given the request: "Make a personal website that runs Game of Life.", We can get the response:  (This is a software development task) should be answered with NO.
# 6. Given the request: "Summarize the document for me.", We can get the response:  (Nothing is provided by the user, requires further information) should be answered with OOD.

# # Instruction
# """

# QUICK_THINK_EXAMPLES ="""
# # Example

# 1. Request: "How to design an online document editing platform that supports real-time collaboration? Please answer me directly.", Response:  (This requires an direct answer) should be answered with QUICK.
# 2. Request: "Help me find some of the latest research papers on deep learning.", Response: (This is a time-sensitive question) should be answered with SEARCH.
# 3. Request: "Tell me the difference between supervised learning and unsupervised learning in machine learning.", Response:  (This is a general knowledge question) should be answered with QUICK.
# 4. Request: "Recommend some programming practice websites suitable for beginners.", Response: (This is a general knowledge question) should be answered with QUICK.
# 5. Request: "Make a personal website that runs Game of Life.", Response:  (This is a software development task) should be answered with TASK.
# 6. Request: "Summarize the document for me.", Response:  (The user needs to provide a link or file path to the document) should be answered with OOD.
# 7. Request: "Optimize our process.", Response:  (Clarification needed: Which specific process? What does "optimize" mean in this context?) should be answered with OOD.

# # Instruction
# """


QUICK_THINK_EXAMPLES ="""
# Example

1. Request: "How to design an online document editing platform that supports real-time collaboration? Please answer me directly.", Response:  The user is asking for a general approach to design a platform, should be answered with QUICK.
2. Request: "Help me find some of the latest research papers on deep learning.", Response: The user is asking for the latest research papers, which is a time-sensitive question, should be answered with SEARCH.
3. Request: "Tell me the difference between supervised learning and unsupervised learning in machine learning.", Response: The user is asking for a general knowledge question, should be answered with QUICK.
4. Request: "Help me develop a one week healthy eating plan.", Response: The user is asking for advice on developing a healthy eating plan. The plan can be provided directly, should be answered with QUICK.
5. Request: "Make a personal website that runs Game of Life.", Response:  The user is asking for a software development task with multiple steps, should be answered with TASK.
6. Request: "Summarize the document for me.", Response:  The user doesn't provide a link or file path to the document, should be answered with OOD.
7. Request: "Optimize our process.", Response:  Optimizing a process is a vague request, and the user needs to clarify what process it is and what is meant by 'optimize', should be answered with OOD.

# Instruction
"""

QUICK_THINK_EXAMPLES ="""
# Example

1. Request: "How do I design an online document editing platform that supports real-time collaboration?"
Thought: This is a direct query about platform design, answerable without additional resources. 
Response Category: QUICK.

2. Request: "What's the difference between supervised and unsupervised learning in machine learning?"
Thought: This is a general knowledge question that can be answered concisely. 
Response Category: QUICK.

3. Request: "Can you help me plan a healthy diet for a week?"
Thought: The user is requesting a simple plan that can be provided immediately. 
Response Category: QUICK.

4. Request: "Can you help me find the latest research papers on deep learning?"
Thought: The user needs current research, requiring a search for the most recent sources. 
Response Category: SEARCH.

5. Request: "Build a personal website that runs the Game of Life simulation."
Thought: This is a detailed software development task that requires multiple steps. 
Response Category: TASK.

6. Request: "Summarize this document for me."
Thought: The request mentions summarizing a document but doesn't provide the document itself, making it impossible to fulfill. 
Response Category: AMBIGUOUS.

7. Request: "Optimize this process." 
Thought: The request is vague and lacks specifics, requiring clarification on the process to optimize.
Response Category: AMBIGUOUS.

8. Request: "Create a poster for our upcoming event." 
Thought: Critical details like event theme, date, and location are missing, making it impossible to complete the task.
Response Category: AMBIGUOUS.

# Instruction
"""

# QUICK_THINK_PROMPT = QUICK_THINK_EXAMPLES + QUICK_THINK_PROMPT
QUICK_THINK_PROMPT = QUICK_THINK_PROMPT.format(examples=QUICK_THINK_EXAMPLES)
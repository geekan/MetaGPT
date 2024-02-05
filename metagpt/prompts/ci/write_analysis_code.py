ASSIGN_TASK_TYPE_PROMPT = """
Please assign a task type to each task in the list below from the given categories:
{task_info}

## All Task Type:
{task_type_desc}
"""

ASSIGN_TASK_TYPE_CONFIG = {
    "name": "assign_task_type",
    "description": "Assign task type to each task by order.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_type": {
                "type": "array",
                "description": "List of task type. The length should as long as task list",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": ["task_type"],
    },
}

TOOL_RECOMMENDATION_PROMPT = """
## User Requirement:
{current_task}

## Task
Recommend up to five tools from 'Available Tools' that can help solve the 'User Requirement'. 

## Available Tools:
{available_tools}

## Tool Selection and Instructions:
- Select tools most relevant to completing the 'User Requirement'.
- If you believe that no tools are suitable, indicate with an empty list.
- Only list the names of the tools, not the full schema of each tool.
- Ensure selected tools are listed in 'Available Tools'.
"""

SELECT_FUNCTION_TOOLS = {
    "name": "select_function_tools",
    "description": "For current task, select suitable tools for it.",
    "parameters": {
        "type": "object",
        "properties": {
            "recommend_tools": {
                "type": "array",
                "description": "List of tool names. Empty list if no tool is suitable.",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": ["recommend_tools"],
    },
}

CODE_GENERATOR_WITH_TOOLS = {
    "name": "add_subtask_code",
    "description": "Add new code cell of current task to the end of an active Jupyter notebook.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The code to be added to a new cell in jupyter.",
            },
        },
        "required": ["code"],
    },
}

TOOL_USAGE_PROMPT = """
# Instruction
Write complete code for 'Current Task'. And avoid duplicating code from finished tasks, such as repeated import of packages, reading data, etc.
Specifically, {tool_type_usage_prompt}

# Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python Class.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

# Available Tools (can be empty):
Each Class tool is described in JSON format. When you call a tool, import the tool first.
{tool_schemas}

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
- Always prioritize using pre-defined tools for the same functionality.
"""

# function in tools, https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
# Reference: https://github.com/KillianLucas/open-interpreter/blob/v0.1.14/interpreter/llm/setup_openai_coding_llm.py
GENERAL_FUNCTION_SCHEMA = {
    "name": "execute",
    "description": "Executes code on the user's machine, **in the users local environment**, and returns the output",
    "parameters": {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "The programming language (required parameter to the `execute` function)",
                "enum": [
                    "python",
                    "R",
                    "shell",
                    "applescript",
                    "javascript",
                    "html",
                    "powershell",
                ],
            },
            "code": {"type": "string", "description": "The code to execute (required)"},
        },
        "required": ["language", "code"],
    },
}

# tool_choice value for general_function_schema
# https://platform.openai.com/docs/api-reference/chat/create#chat-create-tool_choice
GENERAL_TOOL_CHOICE = {"type": "function", "function": {"name": "execute"}}

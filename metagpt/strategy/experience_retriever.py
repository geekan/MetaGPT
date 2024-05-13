from typing import Literal

from pydantic import BaseModel


class ExpRetriever(BaseModel):
    """interface for experience retriever"""

    def retrieve(self, context: str) -> str:
        raise NotImplementedError


class SimpleExpRetriever(ExpRetriever):
    """A simple experience retriever that returns manually crafted examples."""

    EXAMPLE: str = """
    ## example 1
    User Requirement: Create a cli snake game
    Explanation: The requirement is about software development. Assign each tasks to a different team member based on their expertise.
    ```json
    [
        {
            "command_name": "append_task",
            "args": {
                "task_id": "1",
                "dependent_task_ids": [],
                "instruction": "Create a product requirement document (PRD) outlining the features, user interface, and user experience of the CLI snake game.",
                "assignee": "Alice"
            }
        },
        {
            "command_name": "append_task",
            "args": {
                "task_id": "2",
                "dependent_task_ids": ["1"],
                "instruction": "Design the software architecture for the CLI snake game, including the choice of programming language, libraries, and data flow.",
                "assignee": "Bob"
            }
        },
        {
            "command_name": "append_task",
            "args": {
                "task_id": "3",
                "dependent_task_ids": ["2"],
                "instruction": "Break down the architecture into manageable tasks, identify task dependencies, and prepare a detailed task list for implementation.",
                "assignee": "Eve"
            }
        },
        {
            "command_name": "append_task",
            "args": {
                "task_id": "4",
                "dependent_task_ids": ["3"],
                "instruction": "Implement the core game logic for the CLI snake game, including snake movement, food generation, and score tracking.",
                "assignee": "Alex"
            }
        },
        {
            "command_name": "append_task",
            "args": {
                "task_id": "5",
                "dependent_task_ids": ["4"],
                "instruction": "Write comprehensive tests for the game logic and user interface to ensure functionality and reliability.",
                "assignee": "Edward"
            }
        },
        {
            "command_name": "publish_message",
            "args": {
                "content": "User request to create a cli snake game. Please create a product requirement document (PRD) outlining the features, user interface, and user experience of the snake game.",
                "send_to": "Alice"
            }
        },
        {
            "command_name": "reply_to_human",
            "args": {
                "content": "I have assigned the tasks to the team members. Alice will create the PRD, Bob will design the software architecture, Eve will break down the architecture into tasks, Alex will implement the core game logic, and Edward will write comprehensive tests. The team will work on the project accordingly",
            }
        }
    ]
    ```

    ## example 2
    User Requirement: Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.
    Explanation: DON'T decompose requirement if it is a DATA-RELATED task, assign a single task directly to Data Analyst David. He will manage the decomposition and implementation.
    ```json
    [
        {
            "command_name": "append_task",
            "args": {
                "task_id": "1",
                "dependent_task_ids": [],
                "instruction": "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.",
                "assignee": "David"
            }
        },
        {
            "command_name": "publish_message",
            "args": {
                "content": "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.",
                "send_to": "David"
            }
        },
        {
            "command_name": "reply_to_human",
            "args": {
                "content": "I have assigned the task to David. He will break down the task further by himself and starts solving it.",
            }
        }
    ]
    ```

    ## example 3
    Conversation History:
    [
        ...,
        {'role': 'assistant', 'content': 'from Alice(Product Manager) to {'Bob'}: {'docs': {'20240424153821.json': {'root_path': 'docs/prd', 'filename': '20240424153821.json', 'content': '{"Language":"en_us","Programming Language":"Python","Original Requirements":"create a cli snake game","Project Name":"snake_game","Product Goals":["Develop an intuitive and addictive snake game",...], ...}}}}},
    ]
    Explanation: You received a message from Alice, the Product Manager, that she has completed the PRD, use finish_current_task to mark her task as finished and moves the plan to the next task. Based on plan status, next task is for Bob (Architect), publish a message asking him to start. The message content should contain important path info.
    ```json
    [
        {
            "command_name": "finish_current_task",
            "args": {}
        },
        {
            "command_name": "publish_message",
                "args": {
                    "content": "Please design the software architecture for the snake game based on the PRD created by Alice. The PRD is at 'docs/prd/20240424153821.json'. Include the choice of programming language, libraries, and data flow, etc.",
                    "send_to": "Bob"
                }
        },
        {
            "command_name": "reply_to_human",
            "args": {
                "content": "Alice has completed the PRD. I have marked her task as finished and sent the PRD to Bob. Bob will work on the software architecture.",
            }
        }
    ]
    ```

    ## example 4
    User Question: how does the project go?
    Explanation: The user is asking for a general update on the project status. Give a straight answer about the current task the team is working on and provide a summary of the completed tasks.
    ```json
    [
        {
            "command_name": "reply_to_human",
            "args": {
                "content": "The team is currently working on ... We have completed ...",
            }
        }
    ]
    ```
    """

    def retrieve(self, context: str = "") -> str:
        return self.EXAMPLE


class KeywordExpRetriever(ExpRetriever):
    """An experience retriever that returns examples based on keywords in the context."""

    def retrieve(self, context: str, exp_type: Literal["plan", "task"] = "plan") -> str:
        if exp_type == "plan":
            if "deploy" in context.lower():
                return DEPLOY_EXAMPLE
            elif "issue" in context.lower():
                return FIX_ISSUE_EXAMPLE
        elif exp_type == "task":
            if "diagnose" in context.lower():
                return SEARCH_SYMBOL_EXAMPLE
        return ""


DEPLOY_EXAMPLE = """
## example 1
User Requirement: launch a service from workspace/web_snake_game/web_snake_game, and deploy it to public
Explanation: Launching a service requires Terminal tool with daemon mode, write this into task instruction.
```json
[
    {
        "command_name": "append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Use the Terminal tool to launch the service in daemon mode",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Test the service with a simple request",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Deploy the service to public",
            "assignee": "David"
        }
    },
"""


FIX_ISSUE_EXAMPLE = """
## example 1
User Requirement: Write a fix for this issue: https://github.com/xxx/xxx/issues/xxx, and commit and push your changes.
Explanation: The requirement is for software development, focusing on fixing an issue in an existing repository. The process is broken down into several steps, each demanding specific actions and tools.
```json
[
    {
        "command_name": "append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Read the issue description to understand the problem using the Browser tool.",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Clone the repository using the Terminal tool.",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Use Editor to search the relevant function(s), then diagnose and identify the source of the problem.",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Use Editor tool to fix the problem in the corresponding file(s).",
            "assignee": "David"
        }
    },
    {
        "command_name": "append_task",
        "args": {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Commit, push the changes to the repository.",
            "assignee": "David"
        }
    },
]
```
"""


SEARCH_SYMBOL_EXAMPLE = """
## Past Experience
Issue: PaiEasChatEndpoint._call_eas should return bytes type instead of str type
Explanation: To understand the issue, we first need to know the content of the method in the codebase. Therefore, we search the symbol `def _call_eas` in the cloned repo langchain. 

```python
from metagpt.tools.libs.editor import Editor

# Initialize the Editor tool
editor = Editor()
                                                                                                                                                                                                             
# Search for the PaiEasChatEndpoint._call_eas method in the codebase to understand the issue
symbol_to_search = "def _call_eas"
file_block = editor.search_content(symbol=symbol_to_search, root_path="langchain")

# Output the file block containing the method to diagnose the problem
file_block
```
"""

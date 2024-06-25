from typing import Literal

from pydantic import BaseModel


class ExpRetriever(BaseModel):
    """interface for experience retriever"""

    def retrieve(self, context: str) -> str:
        raise NotImplementedError


class DummyExpRetriever(ExpRetriever):
    """A dummy experience retriever that returns empty string."""

    def retrieve(self, context: str = "") -> str:
        return ""


TL_EXAMPLE = """
## example 1
User Requirement: Create a cli snake game using Python.
Explanation: The requirement is about software development. Assign each tasks to a different team member based on their expertise. When publishing message to Product Manager, we copy original user requirement directly to ensure no information loss.
```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Create a product requirement document (PRD) outlining the features, user interface, and user experience of the CLI python snake game.",
            "assignee": "Alice"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Design the software architecture for the CLI snake game, including the choice of programming language, libraries, and data flow.",
            "assignee": "Bob"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Break down the architecture into manageable tasks, identify task dependencies, and prepare a detailed task list for implementation.",
            "assignee": "Eve"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Implement the core game logic for the CLI snake game, including snake movement, food generation, and score tracking.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Write comprehensive tests for the game logic and user interface to ensure functionality and reliability.",
            "assignee": "Edward"
        }
    },
    {
        "command_name": "TeamLeader.publish_message",
        "args": {
            "content": "Create a cli snake game using Python",
            "send_to": "Alice"
        }
    },
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "I have assigned the tasks to the team members. Alice will create the PRD, Bob will design the software architecture, Eve will break down the architecture into tasks, Alex will implement the core game logic, and Edward will write comprehensive tests. The team will work on the project accordingly",
        }
    },
    {
        "command_name": "end"
    }
]
```

## example 2
User Requirement: Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.
Explanation: DON'T decompose requirement if it is a DATA-RELATED task, assign a single task directly to Data Analyst David. He will manage the decomposition and implementation.
```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.",
            "assignee": "David"
        }
    },
    {
        "command_name": "TeamLeader.publish_message",
        "args": {
            "content": "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy.",
            "send_to": "David"
        }
    },
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "I have assigned the task to David. He will break down the task further by himself and starts solving it.",
        }
    },
    {
        "command_name": "end"
    }
]
```

## example 3
Conversation History:
[
    ...,
    {'role': 'assistant', 'content': 'from Alice(Product Manager) to {'Bob'}: {'docs': {'20240424153821.json': {'root_path': 'docs/prd', 'filename': '20240424153821.json', 'content': '{"Language":"en_us","Programming Language":"Python","Original Requirements":"create a cli snake game","Project Name":"snake_game","Product Goals":["Develop an intuitive and addictive snake game",...], ...}}}}},
]
Explanation: You received a message from Alice, the Product Manager, that she has completed the PRD, use Plan.finish_current_task to mark her task as finished and moves the plan to the next task. Based on plan status, next task is for Bob (Architect), publish a message asking him to start. The message content should contain important path info.
```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
    {
        "command_name": "TeamLeader.publish_message",
            "args": {
                "content": "Please design the software architecture for the snake game based on the PRD created by Alice. The PRD is at 'docs/prd/20240424153821.json'. Include the choice of programming language, libraries, and data flow, etc.",
                "send_to": "Bob"
            }
    },
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "Alice has completed the PRD. I have marked her task as finished and sent the PRD to Bob. Bob will work on the software architecture.",
        }
    },
    {
        "command_name": "end"
    }
]
```

## example 4
User Question: how does the project go?
Explanation: The user is asking for a general update on the project status. Give a straight answer about the current task the team is working on and provide a summary of the completed tasks.
```json
[
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "The team is currently working on ... We have completed ...",
        }
    },
    {
        "command_name": "end"
    }
]
```
"""


class SimpleExpRetriever(ExpRetriever):
    """A simple experience retriever that returns manually crafted examples."""

    def retrieve(self, context: str = "") -> str:
        return TL_EXAMPLE


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
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Use the Terminal tool to launch the service in daemon mode",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Test the service with a simple request",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Deploy the service to public",
            "assignee": "David"
        }
    },
]
"""


FIX_ISSUE_EXAMPLE = """
## example 1
User Requirement: Write a fix for this issue: https://github.com/xxx/xxx/issues/xxx, and commit, push your changes, and create a PR to the target repo.
Explanation: The requirement is to fix an issue in an existing repository. The process is broken down into several steps, each demanding specific actions and tools.
```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Read the issue description to understand the problem using the Browser tool.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Clone the repository using the Terminal tool.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Use Editor to search relevant function(s) or open relevant files, then diagnose and identify the source of the problem.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Use Editor tool to fix the problem in the corresponding file(s).",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Commit, push the changes to the repository, and create a pull request to the target repository.",
            "assignee": "David"
        }
    },
]
```
"""


SEARCH_SYMBOL_EXAMPLE = """
## Past Experience 1
Issue: _achat_completion_stream in metagpt/provider/openai_api.py produced TypeError: openai.types.completion_usage.CompletionUsage() argument after ** must be a mapping, not NoneType
Explanation: To understand the issue, we first need to know the content of the method. Since the issue provides the specific file, we should directly search the symbol `def _achat_completion_stream` in that file. Notice in previous steps, we already cd to the cloned project folder, the source code is at `metagpt` under the project folder.
```python
from metagpt.tools.libs.editor import Editor

# Initialize the Editor tool
editor = Editor()
                                                                                                                                                                                                             
# Search for the '_achat_completion_stream' function in the 'openai_api.py' file                                                                                                                               
symbol_to_search = "def _achat_completion_stream"                                                                                                                                                              
file_block = editor.search_content(symbol=symbol_to_search, root_path="metagpt/provider/openai_api.py")

# Output the file block containing the method to diagnose the problem
file_block
```

## Past Experience 2
Issue: PaiEasChatEndpoint._call_eas should return bytes type instead of str type
Explanation: To understand the issue, we first need to know the content of the method. Since no specific file is provided, we can search it in the whole codebase. Therefore, we search the symbol `def _call_eas` in the cloned repo. Notice in previous steps, we already cd to the cloned project folder, the source code is at langchain under the project folder.
```python
from metagpt.tools.libs.editor import Editor

editor = Editor()
                                                                                                                                                                                                             
# Search for the PaiEasChatEndpoint._call_eas method in the codebase to understand the issue
symbol_to_search = "def _call_eas"
file_block = editor.search_content(symbol=symbol_to_search, root_path="langchain")

file_block
```

## Past Experience 3
Issue: When I run main.py, a message 'Running on http://127.0.0.1:5000' will appear on the console, but when I click on this link, the front-end web page cannot be displayed correctly.
Explanation: To understand the issue, we first need to know the content of the file. Since the issue doesn't provide a specific method or class, we will not search_content, but directly open and read the file main.py to diagnose the problem. Notice in previous steps, we already cd to the cloned project folder.
```python
from metagpt.tools.libs.editor import Editor

editor = Editor()
                                                                                                                                                                                                             
# Open the file to understand the issue
editor.read(path="./main.py")
```

## Experience Summary
- When diagnosing an issue, search for the specific symbol in the corresponding file to understand the problem.
- If no specific file is provided, search the symbol in the whole codebase to locate the issue.
- If no specific symbol is provided, directly open and read the file to diagnose the problem.
"""

ENGINEER_EXAMPLE = """
## example 1
User Requirement: Please implement the core game logic for the 2048 game, including tile movements, merging logic, score tracking, and keyboard interaction. Refer to the project schedule located at '/tmp/project_schedule.json' and the system design document at '/tmp/system_design.json' for detailed information.
Explanation: I will first need to read the system design document and the project schedule to understand the specific requirements and architecture outlined for the game development.

```json
[
    {
        "command_name": "Editor.read",
        "args": {
            "path": "/tmp/docs/project_schedule.json"
        }
    },
    {
        "command_name": "Editor.read",
        "args": {
            "path": "/tmp/docs/system_design.json"
        }
    }
]
```

## example 2
To achieve the goal of writing a 2048 game using JavaScript and HTML without any frameworks, I will create a plan consisting of three tasks, each corresponding to the creation of one of the required files: `index.html`, `style.css`, and `script.js`. Following the completion of these tasks, I will add a code review task for each file to ensure the implementation aligns with the provided system design and project schedule documents.

Here's the plan:

1. **Task 1**: Create `index.html` - This file will contain the HTML structure necessary for the game's UI.
2. **Task 2**: Create `style.css` - This file will define the CSS styles to make the game visually appealing and responsive.
3. **Task 3**: Create `script.js` - This file will contain the JavaScript code for the game logic and UI interactions.
4. **Code Review Tasks**: Review each file to ensure they meet the project requirements and adhere to the system design.

Let's start by appending the first task to the plan.

```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Create the index.html file with the basic HTML structure for the 2048 game.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Create the style.css file with the necessary CSS to style the 2048 game.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["1", "2"],
            "instruction": "Create the script.js file containing the JavaScript logic for the 2048 game.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["1"],
            "instruction": "Use ReviewAndRewriteCode to review the code in index.html to ensure it meets the design specifications.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "5",
            "dependent_task_ids": ["2"],
            "instruction": "Use ReviewAndRewriteCode to review the code in style.css to ensure it meets the design specifications.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "6",
            "dependent_task_ids": ["3"],
            "instruction": "Use ReviewAndRewriteCode to review the code in script.js to ensure it meets the design specifications. ",
            "assignee": "Alex"
        }
    }
]
```

## example 3
I will now review the code in `script.js`.
Explanation: to review the code, call ReviewAndRewriteCode.run.

```json
[
    {
        "command_name": "ReviewAndRewriteCode.run",
        "args": {
            "code_path": "/tmp/src/script.js",
            "system_design_input": "/tmp/docs/system_design.json",
            "project_schedule_input": "/tmp/docs/project_schedule.json",
            "code_review_k_times": 2
        }
    }
]
```
"""

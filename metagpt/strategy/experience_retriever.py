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

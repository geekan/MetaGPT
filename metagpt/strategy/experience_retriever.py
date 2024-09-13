from typing import Literal

from pydantic import BaseModel


class ExpRetriever(BaseModel):
    """interface for experience retriever"""

    def retrieve(self, context: str = "") -> str:
        raise NotImplementedError


class DummyExpRetriever(ExpRetriever):
    """A dummy experience retriever that returns empty string."""

    def retrieve(self, context: str = "") -> str:
        return self.EXAMPLE

    EXAMPLE: str = ""


class TRDAllExpRetriever(ExpRetriever):
    def retrieve(self, context: str = "") -> str:
        return self.EXAMPLE

    EXAMPLE: str = """
## example 1
User Requirement: Given some user requirements, write a software framework.
Explanation: Given a complete user requirement, to write a TRD and software framework, you must follow all of the following steps to complete the TRD output required by the user: 1. Call 'write_trd' to generate TRD; 2. Call 'write_framework' to implement TRD into the software framework.
```json
[
    {
        "command_name": "write_trd_and_framework",
        "task_id": "1",
        "dependent_task_ids": [],
        "instruction": "Execute `write_trd_and_framework` to write a TRD and software framework based on user requirements",
        "args": {
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "additional_technical_requirements": "These are additional technical requirements, balabala..."
        }
    }
]
```
## example 2
User Requirement: Given some user requirements, write a software framework.
Explanation: Given a complete user requirement, to write a software framework, you must follow all of the following steps to complete the TRD output required by the user: 1. Call 'write_trd' to generate TRD; 2. Call 'write_framework' to implement TRD into the software framework.
```json
[
    {
        "command_name": "write_trd",
        "task_id": "1",
        "dependent_task_ids": [],
        "instruction": "Execute `write_trd` to write the TRD based on user requirements",
        "args": {
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
        }
    },
    {
        "command_name": "write_framework",
        "task_id": "2",
        "dependent_task_ids": ["1"],
        "instruction": "Execute `write_framework` to write the framework based on the TRD",
        "args": {
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "trd": "<trd> returned by `write_trd`",
            "additional_technical_requirements": "These are additional technical requirements, balabala..."
        }
    }
]
```
## example 3
User Requirement: Given some user requirements, write a TRD, and implement the TRD within a software framework.
Explanation: 
    Given a complete requirement, 要写TRD需要follow如下步骤：
    1. 调用`CompressExternalInterfaces.run`，从acknowledgement中抽取external interfaces的信息；
    2. 按顺序执行如下步骤：
      2.1. 执行`DetectInteraction.run`;
      2.2. 执行`WriteTRD.run`;
      2.3. 执行`EvaluateTRD.run`;
      2.4. 检查`EvaluateTRD.run`的结果：
        2.4.1. 如果`EvaluateTRD.run`的结果被判定为pass，则执行步骤3；
        2.4.2. 如果`EvaluateTRD.run`的结果被判定为deny,则继续执行步骤2；
    3. 按顺序执行如下步骤：
      3.1. 执行`WriteFramework.run`;
      3.2. 执行`EvaluateFramework.run`;
      3.3. 检查`EvaluateFramework.run`的结果：
        3.3.1. 如果`EvaluateFramework.run`的结果被判定为pass，则执行步骤4；
        3.3.2. 如果`EvaluateFramework.run`的结果被判定为deny,则继续执行步骤3；
        3.3.3. 如果已经重复执行步骤3超过9次，则执行步骤4；
    4. 执行`save_framework`,将`WriteFramework.run`的结果保存下来；
```json
[
    {
        "command_name": "CompressExternalInterfaces.run",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
            "acknowledge": "## Interfaces\n balabala..."
        }
    },
    {
        "command_name": "DetectInteraction.run",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
        }
    },
    {
        "command_name": "WriteTRD.run",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Execute `WriteTRD.run` to write TRD",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
            "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`"
        }
    },
    {
        "command_name": "EvaluateTRD.run",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Execute `EvaluateTRD.run` to evaluate the TRD",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
            "interaction_events": "<detected_interaction_events_output>",
            "trd": "<trd> returned by `EvaluateTRD.run`"
        }
    },
    {
        "command_name": "DetectInteraction.run",
        "args": {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "evaluation_conclusion": "<evaluation_conclusion> returned by `EvaluateTRD.run`"
        }
    },
    {
        "command_name": "WriteTRD.run",
        "args": {
            "task_id": "6",
            "dependent_task_ids": ["5"],
            "instruction": "Execute `WriteTRD.run` to write TRD",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
            "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`",
            "previous_version_trd": "<trd> returned by `WriteTRD.run`"
        }
    },
    {
        "command_name": "EvaluateTRD.run",
        "args": {
            "task_id": "7",
            "dependent_task_ids": ["6"],
            "instruction": "Execute `EvaluateTRD.run` to evaluate the TRD",
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
            "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`",
            "trd": "<trd> returned by `WriteTRD.run`",
        }
    },
    {
        "command_name": "WriteFramework.run",
        "args": {
            "task_id": "8",
            "dependent_task_ids": ["7"],
            "instruction": "Execute `WriteFramework.run` to write a software framework according to the TRD",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "trd": "<trd> returned by `WriteTRD.run`",
            "acknowledge": "## Interfaces\n balabala...",
            "additional_technical_requirements": "These are additional technical requirements, balabala...",
        }
    },
    {
        "command_name": "EvaluateFramework.run",
        "args": {
            "task_id": "9",
            "dependent_task_ids": ["8"],
            "instruction": "Execute `EvaluateFramework.run` to evaluate the software framework returned by `WriteFramework.run`",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "trd": "<trd> returned by `WriteTRD.run`",
            "acknowledge": "## Interfaces\n balabala...",
            "legacy_output": "<framework> returned by `WriteFramework.run`",
            "additional_technical_requirements": "These are additional technical requirements, balabala...",
        }
    },
    {
        "command_name": "WriteFramework.run",
        "args": {
            "task_id": "10",
            "dependent_task_ids": ["9"],
            "instruction": "Execute `WriteFramework.run` to write a software framework according to the TRD",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "trd": "<trd> returned by `WriteTRD.run`",
            "acknowledge": "## Interfaces\n balabala...",
            "additional_technical_requirements": "These are additional technical requirements, balabala...",
        }
    },
    {
        "command_name": "EvaluateFramework.run",
        "args": {
            "task_id": "11",
            "dependent_task_ids": ["10"],
            "instruction": "Execute `EvaluateFramework.run` to evaluate the software framework returned by `WriteFramework.run`",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "trd": "<trd> returned by `WriteTRD.run`",
            "acknowledge": "## Interfaces\n balabala...",
            "legacy_output": "<framework> returned by `WriteFramework.run`",
            "additional_technical_requirements": "These are additional technical requirements, balabala...",
        }
    },
    {
        "command_name": "save_framework",
        "args": {
            "task_id": "12",
            "dependent_task_ids": ["11"],
            "instruction": "Execute `save_framework` to save the software framework returned by `WriteFramework.run`",
            "dir_data": "<framework> returned by `WriteFramework.run`",
        }
    }
]
```
    """


class TRDToolExpRetriever(ExpRetriever):
    """A TRD-related experience retriever that returns empty string."""

    def retrieve(self, context: str = "") -> str:
        return self.EXAMPLE

    EXAMPLE: str = """
## example 1
User Requirement: Given some user requirements, write a software framework.
Explanation: Given a complete user requirement, to write a TRD and software framework, you must follow all of the following steps to complete the TRD output required by the user: 1. Call 'write_trd' to generate TRD; 2. Call 'write_framework' to implement TRD into the software framework.
```json
[
    {
        "command_name": "write_trd_and_framework",
        "task_id": "1",
        "dependent_task_ids": [],
        "instruction": "Execute `write_trd_and_framework` to write a TRD and software framework based on user requirements",
        "args": {
            "user_requirements": "This is user requirement balabala...",
            "use_case_actors": "These are actors involved in the use case, balabala...",
            "additional_technical_requirements": "These are additional technical requirements, balabala..."
        }
    }
]
    """
    # EXAMPLE: str = """
    # ## example 1
    # User Requirement: Given some user requirements, write a software framework.
    # Explanation: Given a complete user requirement, to write a software framework, you must follow all of the following steps to complete the TRD output required by the user: 1. Call 'write_trd' to generate TRD; 2. Call 'write_framework' to implement TRD into the software framework.
    # ```json
    # [
    #     {
    #         "command_name": "write_trd",
    #         "task_id": "1",
    #         "dependent_task_ids": [],
    #         "instruction": "Execute `write_trd` to write the TRD based on user requirements",
    #         "args": {
    #             "user_requirements": "This is user requirement balabala...",
    #             "use_case_actors": "These are actors involved in the use case, balabala...",
    #         }
    #     },
    #     {
    #         "command_name": "write_framework",
    #         "task_id": "2",
    #         "dependent_task_ids": ["1"],
    #         "instruction": "Execute `write_framework` to write the framework based on the TRD",
    #         "args": {
    #             "use_case_actors": "These are actors involved in the use case, balabala...",
    #             "trd": "<trd> returned by `write_trd`",
    #             "additional_technical_requirements": "These are additional technical requirements, balabala..."
    #         }
    #     }
    # ]
    # ```
    # """


class TRDExpRetriever(ExpRetriever):
    """A TRD-related experience retriever that returns empty string."""

    def retrieve(self, context: str = "") -> str:
        return self.EXAMPLE

    EXAMPLE: str = """
    ## example 1
    User Requirement: Given some user requirements, write a TRD, and implement the TRD within a software framework.
    Explanation: 
        Given a complete requirement, 要写TRD需要follow如下步骤：
        1. 调用`CompressExternalInterfaces.run`，从acknowledgement中抽取external interfaces的信息；
        2. 按顺序执行如下步骤：
          2.1. 执行`DetectInteraction.run`;
          2.2. 执行`WriteTRD.run`;
          2.3. 执行`EvaluateTRD.run`;
          2.4. 检查`EvaluateTRD.run`的结果：
            2.4.1. 如果`EvaluateTRD.run`的结果被判定为pass，则执行步骤3；
            2.4.2. 如果`EvaluateTRD.run`的结果被判定为deny,则继续执行步骤2；
        3. 按顺序执行如下步骤：
          3.1. 执行`WriteFramework.run`;
          3.2. 执行`EvaluateFramework.run`;
          3.3. 检查`EvaluateFramework.run`的结果：
            3.3.1. 如果`EvaluateFramework.run`的结果被判定为pass，则执行步骤4；
            3.3.2. 如果`EvaluateFramework.run`的结果被判定为deny,则继续执行步骤3；
            3.3.3. 如果已经重复执行步骤3超过9次，则执行步骤4；
        4. 执行`save_framework`,将`WriteFramework.run`的结果保存下来；
    ```json
    [
        {
            "command_name": "CompressExternalInterfaces.run",
            "args": {
                "task_id": "1",
                "dependent_task_ids": [],
                "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
                "acknowledge": "## Interfaces\n balabala..."
            }
        },
        {
            "command_name": "DetectInteraction.run",
            "args": {
                "task_id": "2",
                "dependent_task_ids": ["1"],
                "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
            }
        },
        {
            "command_name": "WriteTRD.run",
            "args": {
                "task_id": "3",
                "dependent_task_ids": ["2"],
                "instruction": "Execute `WriteTRD.run` to write TRD",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
                "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`"
            }
        },
        {
            "command_name": "EvaluateTRD.run",
            "args": {
                "task_id": "4",
                "dependent_task_ids": ["3"],
                "instruction": "Execute `EvaluateTRD.run` to evaluate the TRD",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
                "interaction_events": "<detected_interaction_events_output>",
                "trd": "<trd> returned by `EvaluateTRD.run`"
            }
        },
        {
            "command_name": "DetectInteraction.run",
            "args": {
                "task_id": "5",
                "dependent_task_ids": ["4"],
                "instruction": "Execute `DetectInteraction.run` to extract external interfaces information from acknowledgement.",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "evaluation_conclusion": "<evaluation_conclusion> returned by `EvaluateTRD.run`"
            }
        },
        {
            "command_name": "WriteTRD.run",
            "args": {
                "task_id": "6",
                "dependent_task_ids": ["5"],
                "instruction": "Execute `WriteTRD.run` to write TRD",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
                "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`",
                "previous_version_trd": "<trd> returned by `WriteTRD.run`"
            }
        },
        {
            "command_name": "EvaluateTRD.run",
            "args": {
                "task_id": "7",
                "dependent_task_ids": ["6"],
                "instruction": "Execute `EvaluateTRD.run` to evaluate the TRD",
                "user_requirements": "This is user requirement balabala...",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "available_external_interfaces": "<compressed_external_interfaces_output> returned by `CompressExternalInterfaces.run`",
                "interaction_events": "<detected_interaction_events_output> returned by `DetectInteraction.run`",
                "trd": "<trd> returned by `WriteTRD.run`",
            }
        },
        {
            "command_name": "WriteFramework.run",
            "args": {
                "task_id": "8",
                "dependent_task_ids": ["7"],
                "instruction": "Execute `WriteFramework.run` to write a software framework according to the TRD",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "trd": "<trd> returned by `WriteTRD.run`",
                "acknowledge": "## Interfaces\n balabala...",
                "additional_technical_requirements": "These are additional technical requirements, balabala...",
            }
        },
        {
            "command_name": "EvaluateFramework.run",
            "args": {
                "task_id": "9",
                "dependent_task_ids": ["8"],
                "instruction": "Execute `EvaluateFramework.run` to evaluate the software framework returned by `WriteFramework.run`",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "trd": "<trd> returned by `WriteTRD.run`",
                "acknowledge": "## Interfaces\n balabala...",
                "legacy_output": "<framework> returned by `WriteFramework.run`",
                "additional_technical_requirements": "These are additional technical requirements, balabala...",
            }
        },
        {
            "command_name": "WriteFramework.run",
            "args": {
                "task_id": "10",
                "dependent_task_ids": ["9"],
                "instruction": "Execute `WriteFramework.run` to write a software framework according to the TRD",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "trd": "<trd> returned by `WriteTRD.run`",
                "acknowledge": "## Interfaces\n balabala...",
                "additional_technical_requirements": "These are additional technical requirements, balabala...",
            }
        },
        {
            "command_name": "EvaluateFramework.run",
            "args": {
                "task_id": "11",
                "dependent_task_ids": ["10"],
                "instruction": "Execute `EvaluateFramework.run` to evaluate the software framework returned by `WriteFramework.run`",
                "use_case_actors": "These are actors involved in the use case, balabala...",
                "trd": "<trd> returned by `WriteTRD.run`",
                "acknowledge": "## Interfaces\n balabala...",
                "legacy_output": "<framework> returned by `WriteFramework.run`",
                "additional_technical_requirements": "These are additional technical requirements, balabala...",
            }
        },
        {
            "command_name": "save_framework",
            "args": {
                "task_id": "12",
                "dependent_task_ids": ["11"],
                "instruction": "Execute `save_framework` to save the software framework returned by `WriteFramework.run`",
                "dir_data": "<framework> returned by `WriteFramework.run`",
            }
        }
    ]
    ```
    """


TL_EXAMPLE = """
## example 1
User Requirement: Create a cli snake game.
Explanation: The requirement is about software development. Assign each tasks to a different team member based on their expertise. When publishing message to Product Manager, we copy original user requirement directly to ensure no information loss.
```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Use native HTML for the program. And create a product requirement document (PRD) outlining the features, user interface. ",
            "assignee": "Alice"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Use native HTML for the program. Design the software architecture for the CLI snake game, including the data flow.",
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
            "instruction": "Use native HTML for the program. Implement the core game logic for the CLI snake game, including snake movement, food generation, and score tracking.",
            "assignee": "Alex"
        }
    },
    {
        "command_name": "TeamLeader.publish_message",
        "args": {
            "content": "Use native HTML for the program. Create a cli snake game.",
            "send_to": "Alice"
        }
    },
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "I have assigned the tasks to the team members. Alice will create the PRD, Bob will design the software architecture, Eve will break down the architecture into tasks, Alex will implement the core game logic, and Edward will write comprehensive tests. The team will work on the project accordingly"
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
    {'role': 'assistant', 'content': 'from Alice(Product Manager) to {'<all>'}: Request is completed, with outputs: Command WritePRD executed: PRD filename: "/tmp/workspace/snake_game/docs/prd.json"'},
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
                "content": "Please design the software architecture for the snake game based on the PRD created by Alice. The PRD is at '/tmp/workspace/snake_game/docs/prd.json'. Include the choice of programming language, libraries, and data flow, etc.",
                "send_to": "Bob"
            }
    },
    {
        "command_name": "RoleZero.reply_to_human",
        "args": {
            "content": "Alice has completed the PRD. I have marked her task as finished and sent the PRD to Bob. Bob will work on the software architecture."
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
            "content": "The team is currently working on ... We have completed ..."
        }
    },
    {
        "command_name": "end"
    }
]
```

## example 5
OBSERVATION : current task is none and all task is finished.
Explanation: Last task is "Plan.finish_current_task" or 'RoleZero.reply_to_human' and now the current task is none, it means everything is done.Just coutput command "end".
```json
[
    {
        "command_name": "end"
    }
]

## example 6
OBSERVATION : The previously completed task is identical to the current task.
Explanation: The current task has been accomplished previously.
```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
]
```

## example 7
OBSERVATION : the task assigned to Alice is still ongoing as it has not been marked as finished. The current task in the plan is for Alice to create the PRD.
Explanation: "I attempted to locate historical records containing 'send to [<all>]', and discovered an entry stating 'PRD is finished and masked.' This indicates that Alice's task has been completed.
```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
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
            elif "https:" in context.lower() or "http:" in context.lower() or "search" in context.lower():
                if "search" in context.lower() or "click" in context.lower():
                    return WEB_SCRAPING_EXAMPLE
                return WEB_SCRAPING_EXAMPLE_SIMPLE
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
Explanation: I will first need to read the system design document and the project schedule to understand the specific requirements and architecture outlined for the game development. I should NOT create tasks at this stage.

```json
[
    {
        "command_name": "Editor.read",
        "args": {
            "path": "/tmp/project_schedule.json"
        }
    },
    {
        "command_name": "Editor.read",
        "args": {
            "path": "/tmp/system_design.json"
        }
    }
]
```

## example 2
Consider this example only after you have obtained the content of system design and project schedule documents.
Suppose the system design and project schedule prescribes three files index.html, style.css, script.js, to follow the design and schedule, I will create a plan consisting of three tasks, each corresponding to the creation of one of the required files: `index.html`, `style.css`, and `script.js`. 

Here's the plan:

1. **Task 1**: Create `index.html` - This file will contain the HTML structure necessary for the game's UI.
2. **Task 2**: Create `style.css` - This file will define the CSS styles to make the game visually appealing and responsive.
3. **Task 3**: Create `script.js` - This file will contain the Pure JavaScript code for the game logic and UI interactions.

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
            "instruction": "Create the script.js file containing the Pure JavaScript logic for the 2048 game.",
            "assignee": "Alex"
        }
    }
]
```

## example 3
Explanation: Take on one task, such as writing a file. Upon completion, finish current task

```json
[
    {
        "command_name": "Engineer2.write_new_code",
        "args": {
            "path": "src/index.html"
        }
    },
    {
        "command_name": "Plan.finish_current_task",
        "args": {{}}
    }
]
```

## example 4
I have received a GitHub issue URL.
I will use browser to review the detailed information of this issue in order to understand the problem.
```json
[
    {
        "command_name": "Browser.goto",
        "args": {
            "url": "https://github.com/geekan/MetaGPT/issues/1275"
        }
    }
]
```

## example 6
I need to locating the `openai_api.py` file, so I will search for the `openai_api.py` file.
```json
[
    {
        "command_name": "Editor.find_file",
        "args": {
            "file_name": "openai_api.py"   
        }
    }
]
```



## example 7
I have located the openai_api.py file. I want to edit this file, so I will open it first.
```json
[
    {
        "command_name": "Editor.open_file",
        "args": {
            "path": "/workspace/MetaGPT/provider/openai_api.py"   
        }
    }
]
```

## example 8
I have opened the openai_api.py file. However, the range of lines shown is from 001 to 100, and I want to see more. Therefore, I want to use the scroll_down command to view additional lines.
```json
[
    {
        "command_name": "Editor.scroll_down",
        "args": {{}}
    }
]
```

## example 9
I've found the bug and will start fixing it. I'll pay close attention to the indentation.
Since I only need to modify a few lines in this file, I will use Editor.edit_file_by_replace. The original content will be replaced by the new code.
Editor tool is exclusive. If I use this tool, I cannot use any other commands in the current response.
```json
[
    {
        "command_name": "Editor.edit_file_by_replace",
        "args": {
            "file_name":"/workspace/MetaGPT/provider/openai_api.py",
            "to_replace": "            inv_trig_table = ["asin", "acos", "atan", "acot"]"
            "new_content": "            inv_trig_table = ["asin", "acos", "atan", "acsc", "asec", "acot"]"
        }
    }
]
```

## example 10
I only need to add a few lines to the file, so I will use Editor.insert_content_at_line. The new code will not cover the original code.
Note that the Editor command must be executed in a single response, so this step will only involve using the Editor command.
```json
[
    {
        "command_name": "Editor.insert_content_at_line",
        "args": {
            "file_name":"/workspace/MetaGPT/provider/openai_api.py"
            "line_number":727,
            "content": "if hasattr(self, '_print_' + func) and not isinstance(expr.func, UndefinedFunction):\\n            return getattr(self, '_print_' + func)(expr, exp)"
        }
    }
]
```

## example 10.1
To enhance the functionality of the 2048 game, including game end detection and score tracking, we need to add these features to the existing game_2048.py file. First, we will add a score tracking feature, and then we will insert game end detection logic into the game loop.
We will use the Editor.insert_content_at_line command to insert new code into the file for adding score tracking and game end detection.
Since Editor.insert_content_at_line can only be used once per response, this time I will use it to create the variable self.score
```json
[
    {
        "command_name": "Editor.insert_content_at_line",
        "args": {
            "file_name": "/home/mgx/mgx/MetaGPT/workspace/2048_game_py/game_2048.py",
            "line_number": 4,
            "content": "        self.score = 0\n"
        }
    }
]
```
In the next turn, I will try to add another code snippet

## example 11

Create a pull request (Optional): Merge the changes from the new branch into the master branch.
Thought: Now that the changes have been pushed to the remote repository, due to the user's requirement, let's create a pull request to merge the changes into the master branch.
```json
[
    {
        "command_name": "git_create_pull",
        "args": {
            "base": "master",
            "head": "test-fix",
            "base_repo_name": "garylin2099/MetaGPT",
            "head_repo_name": "seeker-jie/MetaGPT",
            "app_name": "github",
            "title": "Fix Issue #1275: produced TypeError: openai.types.completion_usage.CompletionUsage() argument after ** must be a mapping, not NoneType"",
            "body": "This pull request addresses issue #1275 by ensuring that chunk.usage is not None before passing it to CompletionUsage."
            }
        }
]
```
"""

WEB_SCRAPING_EXAMPLE = """
## action 1
User Requirement: Scrap and list the restaurant names of first page by searching for the keyword `beef` on the website https://www.yelp.com/.
Explanation: The requirement is to scrape data from a website and extract information about restaurants. The process involves searching for restaurants with a specific keyword, retrieving and presenting the data in a structured format.

```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Navigate to the yelp website.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Search for restaurants with the keyword 'beef'.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "View and print the html content of the search result page before scrap data to understand the structure.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Parse the html content to scrape the restaurant names and print it.",
            "assignee": "David"
        }
    }
]
```

## action 2
Explanation: To search for restaurants, I will now go to the website https://www.yelp.com/ first.

```json
[
    {
        "command_name": "Browser.goto",
        "args": {
            "url": "https://www.yelp.com/"
        }
    }
]
```

## action 3
Explanation: Since the Browser has successfully navigated to the website, and I find that the element id of the search box is 53. I will finish the current task and then use the Browser tool to type the keyword `beef` in the search box and press enter.

```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
    {
        "command_name": "Browser.type",
        "args": {
            "element_id": 53,
            "content": "beef",
            "press_enter_after": true
        }
    }
]
```

## action 4
Explanation: Since the Browser has successfully search the keyword `beef`, I will finish the current task and then write code to view and print the html content of the page.

```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
    {
        "command_name": "DataAnalyst.write_and_exec_code",
        "args": {}
    }
]
```

## action 5
Explanation: Since I has successfully viewed the html content in the context, I will first finish the current task and then write code to parse the html content and extract the restaurant names.

```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
    {
        "command_name": "DataAnalyst.write_and_exec_code",
        "args": {}
    }
]

...
"""


WEB_SCRAPING_EXAMPLE_SIMPLE = """
## action 1
User Requirement: List the restaurant names on the website https://www.yelp.com/search?find_desc=beef&find_loc=New+York%2C+NY.
Explanation: The requirement is to scrape data from a website and extract information about restaurants. The process involves retrieving and presenting the data in a structured format.

```json
[
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "View and print the html content of the page before scrap data to understand the structure.",
            "assignee": "David"
        }
    },
    {
        "command_name": "Plan.append_task",
        "args": {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Parse the html content to scrape the restaurant names and print it.",
            "assignee": "David"
        }
    }
]
```

## action 2
Explanation: To scrap data from the website, I will first view and print the html content of the page.

```json
[
    {
        "command_name": "DataAnalyst.write_and_exec_code",
        "args": {}
    }
]
```

## action 3
Explanation: Since I has successfully viewed the html content in the context, I will first finish the current task and then write code to parse the html content and extract the restaurant names.
    
```json
[
    {
        "command_name": "Plan.finish_current_task",
        "args": {}
    },
    {
        "command_name": "DataAnalyst.write_and_exec_code",
        "args": {}
    }
]
```
...
"""

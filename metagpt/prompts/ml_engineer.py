#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_engineer
# @Desc    :
GEN_DATA_DESC_PROMPT = """
Here is the head 5 rows of the dataset:
{data_head}

Please provide a brief one-sentence background of the dataset, and concise descriptions for each column. Keep descriptions short yet informative.

Output the information in a JSON format, as shown in this example:
```json
{
    "data_desc": "Brief dataset background.",
    "column_desc": {
        "column_name1": "Description of the first column.",
        "column_name2": "Description of the second column.",
        ...
    }
}
```
"""

ASSIGN_TASK_TYPE_PROMPT = """
Please assign a task type to each task in the list below from the given categories:
{task_list}

## All Task Type:
- **feature_engineering**: Only for creating new columns for input data.
- **data_preprocess**: Only for changing value inplace.
- **model_train**: Only for training model.
- **other**: Any tasks that do not fit into the previous categories, such as visualization, summarizing findings, build model, etc.
"""

ASSIGN_TASK_TYPE = {
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
Your are a tool recommender, the main goal is to recommend suitable tools for current task before coding. A tool means a function that can be used to help you solve the task.

## List of Available Tools:
{available_tools}

This is a task guide for the current task, including detailed code steps. You can refer to it when recommending tools.
{code_steps}

## Tool Selection and Instructions:
- For the task, choose up to five tools that are most likely to be useful in solving the task.
- If you believe that no tools are suitable, indicate with an empty list.
- Only list the names of the tools, not the full schema of each tool.
- The result should only contain tool names that are in the list of available tools.
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
## Target
{goal}

## History Info
{context}

## Available Tools:
Each function is described in JSON format, including the function name and parameters. {output_desc}
{function_catalog}

When you call a function above, you should import the function from `{module_name}` first, e.g.:
```python
from metagpt.tools.functions.libs.data_preprocess import fill_missing_value
```end

## Your Output Format:
Generate the complete code for this task:
```python
# Tools used: [function names or 'none']
<your code for the current task, without any comments>
```end

## Attention:
Make sure use the columns from the dataset columns
Finish your coding tasks as a helpful programmer based on the tools.

"""
GENERATE_CODE_PROMPT = """
## Target
{goal}

## History Info
{context}

## Your Output Format:
Generate the complete code for this task:
```python
# Tools used: [function names or 'none']
<your code for the current task>
```end

## Attention:
Make sure use the columns from the dataset columns
Finish your coding tasks as a helpful programmer based on the tools.

"""

TOO_ORGANIZATION_PROMPT = """
The previous conversation has provided all tasks step-by-step for the use goal and their statuses. 
Now, begin writing code for the current task. This code should writen strictly on the basis of all previous completed tasks code, not a standalone code. And avoid writing duplicate code that has already been written in previous tasks, such as repeated import of packages, reading data, etc.
Specifically, {special_prompt}
You can utilize pre-defined tools in 'Available Tools' if the tools are sufficient. And you should combine the use of other public packages if necessary, like sklearn, numpy, pandas, etc..

## Code Steps for Current Task:
Follow steps below when you writing code if it's convenient.
{code_steps}

## Available Tools:
Each function is described in JSON format, including the function name and parameters. {output_desc}
{function_catalog}

When you call a function above, you should import the function from `{module_name}` first, e.g.:
```python
from metagpt.tools.functions.libs.data_preprocess import fill_missing_value
```end

## Your Output Format:
Generate the complete code for this task:
```python
# Tools used: [function names or 'none']
<your code for the current task, without any comments>
```end

*** Important Rules ***
- If you use tool not in the list, you should implement it by yourself.
- Ensure the output new code is executable in the same Jupyter notebook environment with previous tasks code have been executed.
- When write code for current task, remember the code should be coherent with previous tasks code.
- Remember that don't process the columns have been processed in previous tasks and don't mock data yourself.
- Prioritize using tools for the same functionality.
"""

DATA_PREPROCESS_PROMPT = """
The current task is about data preprocessing, closely monitor each column's data type. Apply suitable methods for various types (numerical, categorical, datetime, textual, etc.) to ensure the pandas.DataFrame is correctly formatted.
Additionally, ensure that the columns being processed must be the ones that actually exist in the dataset.
Don't write processed data to files.
"""

FEATURE_ENGINEERING_PROMPT = """
The current task is about feature engineering. when performing it, please adhere to the following principles:
- Ensure that the feature you're working with is indeed present in the dataset and consider the data type (numerical, categorical, etc.) and application scenario (classification, regression tasks, etc.).
- When generate new features, you should combine real world knowledge and decide what features are useful for the task.
- Generate as diverse features as possible to improve the model's performance.
- Before generating a new feature, ensure the used features are already processed and ready to use.
"""

MODEL_TRAIN_PROMPT = """
The current task is about training a model, please ensure high performance:
- Keep in mind that your user prioritizes results and is highly focused on model performance. So, when needed, feel free to use models of any complexity to improve effectiveness, such as lightGBM, XGBoost, CatBoost, etc.
- Before training, first check not is_numeric_dtype columns and use label encoding to convert them to numeric columns.
- Use the data from previous task result directly, do not mock or reload data yourself.
"""

DATA_PREPROCESS_OUTPUT_DESC = "Please note that all functions uniformly output a processed pandas.DataFrame, facilitating seamless integration into the broader workflow."

FEATURE_ENGINEERING_OUTPUT_DESC = "Please note that all functions uniformly output updated pandas.DataFrame with feature engineering applied."

CLASSIFICATION_MODEL_OUTPUT_DESC = ""

REGRESSION_MODEL_OUTPUT_DESC = ""

ML_SPECIFIC_PROMPT = {
    "data_preprocess": DATA_PREPROCESS_PROMPT,
    "feature_engineering": FEATURE_ENGINEERING_PROMPT,
    "model_train": MODEL_TRAIN_PROMPT,
}

TOOL_OUTPUT_DESC = {
    "data_preprocess": DATA_PREPROCESS_OUTPUT_DESC,
    "feature_engineering": FEATURE_ENGINEERING_OUTPUT_DESC,
}

ML_MODULE_MAP = {
    "data_preprocess": "metagpt.tools.functions.libs.data_preprocess",
    "feature_engineering": "metagpt.tools.functions.libs.feature_engineering",
}

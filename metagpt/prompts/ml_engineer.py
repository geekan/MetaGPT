#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_engineer
# @Desc    :
UPDATE_DATA_COLUMNS = """
# Background
Keep dataset column information updated before model train.
## Done Tasks
```python
{history_code}
```end

# Task
Update and print the dataset's column information only if the train or test data has changed. Use the following code:
```python
from metagpt.tools.functions.libs.data_preprocess import get_column_info

column_info = get_column_info(df)
print("column_info")
print(column_info)
```end

# Constraints:
- Use the DataFrame variable from 'Done Tasks' in place of df.
- Import `get_column_info` only if it's not already imported.
"""

GEN_DATA_DESC_PROMPT = """
Here is the head 5 rows of the dataset:
{data_head}

Please provide a brief one-sentence background of the dataset, and concise meaning for each column. Keep descriptions short.

Output the information in a JSON format, as shown in this example:
```json
{
    "data_desc": "Brief dataset background.",
    "column_desc": {
        "column_name1": "Abstract meaning of the first column.",
        "column_name2": "Abstract meaning of the second column.",
        ...
    }
}
```

# Constraints:
- Don't contain specific values or examples found in the data column.
"""

ASSIGN_TASK_TYPE_PROMPT = """
Please assign a task type to each task in the list below from the given categories:
{task_list}

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
This is a detailed code steps for current task. You can refer to it when recommending tools.
{code_steps}

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


PRINT_DATA_COLUMNS = {
    "name": "print_column_info",
    "description": "Print the latest column information after 'Done Tasks' code if first read or data changed.",
    "parameters": {
        "type": "object",
        "properties": {
            "is_update": {
                "type": "boolean",
                "description": "Whether need to update the column info.",
            },
            "code": {
                "type": "string",
                "description": "The code to be added to a new cell in jupyter.",
            },
        },
        "required": ["is_update", "code"],
    },
}

GENERATE_CODE_PROMPT = """
# Background
As a data scientist, you need to help user to achieve their goal [{user_requirement}] step-by-step in an continuous Jupyter notebook.

## Done Tasks
```python
{history_code}
```end

## Current Task
{current_task}

# Latest Data Info
Latest data info after previous tasks:
{column_info}

# Task
Write complete code for 'Current Task'. And avoid duplicating code from 'Done Tasks', such as repeated import of packages, reading data, etc.
Specifically, {special_prompt}

# Code Steps:
Strictly follow steps below when you writing code if it's convenient.
{code_steps}

# Output Example:
when current task is "train a lightgbm model on training data", and their are two steps in 'Code Steps', the code be like:
```python
# Step 1: check data type and convert to numeric
ojb_cols = train.select_dtypes(include='object').columns.tolist()

for col in obj_cols:
    encoder = LabelEncoder()
    train[col] = encoder.fit_transform(train[col].unique().tolist() + ['unknown'])
    test[col] = test[col].apply(lambda x: x if x in encoder.classes_ else 'unknown')
    test[col] = encoder.transform(test[col])

# Step 2: train lightgbm model
model = LGBMClassifier()
model.fit(train, y_train)
```end

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
- The output code should contain all steps implemented in 'Code Steps'.
"""

TOOL_USAGE_PROMPT = """
# Instruction
Write complete code for 'Current Task'. And avoid duplicating code from finished tasks, such as repeated import of packages, reading data, etc.
Specifically, {special_prompt}

# Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python Class.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

# Available Tools (can be empty):
Each Class tool is described in JSON format. When you call a tool, import the tool first.
{tool_catalog}

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
- Always prioritize using pre-defined tools for the same functionality.
"""

ML_TOOL_USAGE_PROMPT = """
# Background
As a data scientist, you need to help user to achieve their goal [{user_requirement}] step-by-step in an continuous Jupyter notebook.

## Done Tasks
```python
{history_code}
```end

## Current Task
{current_task}

# Latest Data Info
Latest data info after previous tasks:
{column_info}

# Task
Write complete code for 'Current Task'. And avoid duplicating code from 'Done Tasks', such as repeated import of packages, reading data, etc.
Specifically, {special_prompt}

# Code Steps:
Strictly follow steps below when you writing code if it's convenient.
{code_steps}

# Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python Class.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

# Available Tools:
Each Class tool is described in JSON format. When you call a tool, import the tool from `{module_name}` first.
{tool_catalog}

# Output Example:
when current task is "do data preprocess, like fill missing value, handle outliers, etc.", and their are two steps in 'Code Steps', the code be like:
```python
# Step 1: fill missing value
# Tools used: ['FillMissingValue']
from metagpt.tools.functions.libs.data_preprocess import FillMissingValue

train_processed = train.copy()
test_processed = test.copy()
num_cols = train_processed.select_dtypes(include='number').columns.tolist()
if 'label' in num_cols:
    num_cols.remove('label')
fill_missing_value = FillMissingValue(features=num_cols, strategy='mean')
fill_missing_value.fit(train_processed)
train_processed = fill_missing_value.transform(train_processed)
test_processed = fill_missing_value.transform(test_processed)

# Step 2: handle outliers
for col in num_cols:
    low, high = train_processed[col].quantile([0.01, 0.99])
    train_processed[col] = train_processed[col].clip(low, high)
    test_processed[col] = test_processed[col].clip(low, high)
```end

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
- Always prioritize using pre-defined tools for the same functionality.
- Always copy the DataFrame before processing it and use the copy to process.
- The output code should contain all steps implemented correctly in 'Code Steps'.
"""
# - If 'Code Steps' contains step done in 'Done Tasks', such as reading data, don't repeat it.

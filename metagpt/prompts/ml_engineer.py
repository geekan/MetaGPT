#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_engineer
# @Desc    :
UPDATE_DATA_COLUMNS = """
# Background
Keep dataset column information updated to reflect changes in training or testing datasets, aiding in informed decision-making during data analysis.
## Done Tasks
```python
{history_code}
```end

# Task
Update and print the dataset's column information only if the train or test data has changed. Use the following code:
```python
from metagpt.tools.functions.libs.data_preprocess import get_column_info

column_info = get_column_info(df)
print("df_column_info")
print(column_info)
```end

# Constraints:
- Use the DataFrame variable from 'Done Tasks' in place of df.
- Import `get_column_info` only if it's not already imported.
- Skip update if no changes in training/testing data, except for initial data load.
- No need to update info if only model evaluation is performed.
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
- **feature_engineering**: Only for creating new columns for input data.
- **data_preprocess**: Only for changing value inplace.
- **model_train**: Only for training model.
- **model_evaluate**: Only for evaluating model.
- **other**: Any tasks that do not fit into the previous categories, such as visualization, summarizing findings, etc.
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
    train[col] = encoder.fit_transform(train[col])
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
#- If 'Code Steps' contains step done in 'Done Tasks', such as reading data, don't repeat it.

DATA_PREPROCESS_PROMPT = """
The current task is about data preprocessing, please note the following:
- Monitor data types per column, applying appropriate methods.
- Ensure operations are on existing dataset columns.
- Avoid writing processed data to files.
- Prefer alternatives to one-hot encoding for categorical data.
- Only encode necessary categorical columns to allow for potential feature-specific engineering tasks later.
"""

FEATURE_ENGINEERING_PROMPT = """
The current task is about feature engineering. when performing it, please adhere to the following principles:
- Ensure operations are on existing dataset columns and consider the data type (numerical, categorical, etc.) and application scenario (classification, regression tasks, etc.).
- Create impactful features based on real-world knowledge and column info.
- Generate as diverse features as possible to improve the model's performance.
- If potential impactful features are not included in 'Code Steps', add new steps to generate them.
"""

MODEL_TRAIN_PROMPT = """
The current task is about training a model, please ensure high performance:
- Keep in mind that your user prioritizes results and is highly focused on model performance. So, when needed, feel free to use models of any complexity to improve effectiveness, such as lightGBM, XGBoost, CatBoost, etc.
- Before training, first check not is_numeric_dtype columns and use label encoding to convert them to numeric columns.
- Use the data from previous task result directly, do not mock or reload data yourself.
"""

MODEL_EVALUATE_PROMPT = """
The current task is about evaluating a model, please note the following:
- Ensure that the evaluated data is same processed as the training data. If not, remember use object in 'Done Tasks' to transform the data.
- Use trained model from previous task result directly, do not mock or reload model yourself.
"""

ML_SPECIFIC_PROMPT = {
    "data_preprocess": DATA_PREPROCESS_PROMPT,
    "feature_engineering": FEATURE_ENGINEERING_PROMPT,
    "model_train": MODEL_TRAIN_PROMPT,
    "model_evaluate": MODEL_EVALUATE_PROMPT,
}

ML_MODULE_MAP = {
    "data_preprocess": "metagpt.tools.functions.libs.data_preprocess",
    "feature_engineering": "metagpt.tools.functions.libs.feature_engineering",
    "udf": "metagpt.tools.functions.libs.udf",
}

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Data Description
{data_desc}
## Current Plan
{tasks}
## Current Task
{current_task}
"""

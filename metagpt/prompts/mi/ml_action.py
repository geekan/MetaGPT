#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_action
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
from metagpt.tools.libs.data_preprocess import get_column_info

column_info = get_column_info(df)
print("column_info")
print(column_info)
```end

# Constraints:
- Use the DataFrame variable from 'Done Tasks' in place of df.
- Import `get_column_info` only if it's not already imported.
"""

PRINT_DATA_COLUMNS = {
    "name": "print_column_info",
    "description": "Print the latest column information after 'Done Tasks' code if first read or data changed.",
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

ML_COMMON_PROMPT = """
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
Specifically, {tool_type_usage_prompt}
"""

USE_NO_TOOLS_EXAMPLE = """
# Output Example:
when current task is "train a lightgbm model on training data", the code can be like:
```python
# Step 1: check data type and convert to numeric
obj_cols = train.select_dtypes(include='object').columns.tolist()

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
"""

USE_TOOLS_EXAMPLE = """
# Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python Class.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

# Available Tools:
Each Class tool is described in JSON format. When you call a tool, import the tool from its path first.
{tool_schemas}

# Output Example:
when current task is "do data preprocess, like fill missing value, handle outliers, etc.", the code can be like:
```python
# Step 1: fill missing value
# Tools used: ['FillMissingValue']
from metagpt.tools.libs.data_preprocess import FillMissingValue

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
"""

ML_GENERATE_CODE_PROMPT = ML_COMMON_PROMPT + USE_NO_TOOLS_EXAMPLE
ML_TOOL_USAGE_PROMPT = ML_COMMON_PROMPT + USE_TOOLS_EXAMPLE

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_engineer
# @Desc    :
TOOL_RECOMMENDATION_PROMPT = """
## Comprehensive Task Description:
{task}

## Dataset Description:
Details about the dataset for the project:
{data_desc}

This task is divided into several steps, and you need to select the most suitable tools for each step. A tool means a function that can be used to help you solve the task.

## Detailed Code Steps for the Task:
{code_steps}

## List of Available Tools:
{available_tools}

## Tool Selection and Instructions:
- For each code step listed above, choose up to five tools that are most likely to be useful in solving the task.
- If you believe that no tools are suitable for a step, indicate with an empty list.
- Only list the names of the tools, not the full schema of each tool.
- The result should only contain tool names that are in the list of available tools.
- The result list should be in the same order as the code steps.
"""

SELECT_FUNCTION_TOOLS = {
    "name": "select_function_tools",
    "description": "Given code steps to generate full code for a task, select suitable tools for each step by order.",
    "parameters": {
        "type": "object",
        "properties": {
            "recommend_tools": {
                "type": "array",
                "description": "List of tool names for each code step. Empty list if no tool is suitable.",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
        "required": ["recommend_tools"],
    },
}


CODE_GENERATOR_WITH_TOOLS = {
    "name": "add_subtask_code",
    "description": "Add new code of current subtask to the end of an active Jupyter notebook.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The code to be added.",
            },
        },
        "required": ["code"],
    },
}

TOO_ORGANIZATION_PROMPT = """
As a senior data scientist, your role involves developing code for a specific sub-task within a larger project. This project is divided into several sub-tasks, which may either be new challenges or extensions of previous work.

## Sub-tasks Overview
Here's a list of all the sub-tasks, indicating their current status (DONE or TODO). Your responsibility is the first TODO task on this list.
{all_tasks}

## Historical Code (Previously Done Sub-tasks):
This code, already executed in the Jupyter notebook, is critical for understanding the background and foundation for your current task.
```python
{completed_code}
```

## Dataset Description:
Details about the dataset for the project:
{data_desc}

## Current Task Notion:
{special_prompt}

## Code Steps for Your Sub-task:
Follow these steps to complete your current TODO task. You may use external Python functions or write custom code as needed. Ensure your code is self-contained.
{code_steps}

When you call a function, you should import the function from `{module_name}` first, e.g.:
```python
from metagpt.tools.functions.libs.feature_engineering import fill_missing_value
```

## Available Functions for Each Step:
Here's a list of all available functions for each step. You can find more details about each function in [## Function Catalog]
{available_tools}

## Function Catalog:
Each function is described in JSON format, including the function name and parameters. {output_desc}
{function_catalog}

## Your Output Format:
Generate the complete code for every step, listing any used function tools at the beginning of the step:
```python
# Step 1
# Tools used: [function names or 'none']
<your code for this step, without any comments>

# Step 2
# Tools used: [function names or 'none']
<your code for this step, without any comments>

# Continue with additional steps, following the same format...
```end

*** Important Rules ***
- Use only the tools designated for each code step.
- Your output should only include code for the current sub-task. Don't repeat historical code.
- Only mention functions in comments if used in the code.
- Ensure the output new code is executable in the current Jupyter notebook environment, with all historical code executed.
"""


DATA_PREPROCESS_PROMPT = """
In data preprocessing, closely monitor each column's data type. Apply suitable methods for various types (numerical, categorical, datetime, textual, etc.) to ensure the pandas.DataFrame is correctly formatted.
Additionally, ensure that the columns being processed must be the ones that actually exist in the dataset.
"""

FEATURE_ENGINEERING_PROMPT = """
When performing feature engineering, please adhere to the following principles:
- For specific user requests (such as removing a feature, creating a new feature based on existing data), directly generate the corresponding code.
- In cases of unclear user requirements, write feature engineering code that you believe will most improve model performance. This may include feature transformation, combination, aggregation, etc., with a limit of five features at a time.
- Ensure that the feature you're working with is indeed present in the dataset and consider the data type (numerical, categorical, etc.) and application scenario (classification, regression tasks, etc.).
- Importantly, provide detailed comments explaining the purpose of each feature and how it might enhance model performance, especially when the features are generated based on semantic understanding without clear user directives.
"""

CLASSIFICATION_MODEL_PROMPT = """
"""

REGRESSION_MODEL_PROMPT = """
"""

DATA_PREPROCESS_OUTPUT_DESC = "Please note that all functions uniformly output a processed pandas.DataFrame, facilitating seamless integration into the broader workflow."

FEATURE_ENGINEERING_OUTPUT_DESC = "Please note that all functions uniformly output updated pandas.DataFrame with feature engineering applied."

CLASSIFICATION_MODEL_OUTPUT_DESC = ""

REGRESSION_MODEL_OUTPUT_DESC = ""


ML_SPECIFIC_PROMPT = {
    "data_preprocess": DATA_PREPROCESS_PROMPT,
    "feature_engineering": FEATURE_ENGINEERING_PROMPT,
    "classification_model": CLASSIFICATION_MODEL_PROMPT,
    "regression_model": REGRESSION_MODEL_PROMPT,
}

TOOL_OUTPUT_DESC = {
    "data_preprocess": DATA_PREPROCESS_OUTPUT_DESC,
    "feature_engineering": FEATURE_ENGINEERING_OUTPUT_DESC,
    "classification_model": CLASSIFICATION_MODEL_OUTPUT_DESC,
    "regression_model": REGRESSION_MODEL_OUTPUT_DESC,
}

ML_MODULE_MAP = {
    "data_preprocess": "metagpt.tools.functions.libs.machine_learning.data_preprocess",
    "feature_engineering": "metagpt.tools.functions.libs.machine_learning.feature_engineering",
    "classification_model": "metagpt.tools.functions.libs.machine_learning.ml_model",
    "regression_model": "metagpt.tools.functions.libs.machine_learning.ml_model",
}

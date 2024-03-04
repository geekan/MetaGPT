STRUCTUAL_PROMPT = """
# Background
As a data scientist, you need to help user to achieve their goal [{user_requirement}] step-by-step in an continuous Jupyter notebook. Since it is a notebook environment, don't use asyncio.run. Instead, use await if you need to call an async function.

# Finished Tasks
## code
```python
{code_written}
```

## execution result
{task_results}

# Current Task
{current_task}

# Instruction
Write complete code for 'Current Task'. And avoid duplicating code from 'Finished Tasks', such as repeated import of packages, reading data, etc.
Specifically, {tool_type_usage_prompt}

# Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python class or function.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

# Available Tools:
Each tool is described in JSON format. When you call a tool, import the tool from its path first.
{tool_schemas}

# Examples
{examples}

# Output
Output code in the following format:
```python
your code
```
"""

DEBUG_REFLECTION_EXAMPLE = '''
[previous impl]:
assistant:
```python
def add(a: int, b: int) -> int:
   """
   Given integers a and b, return the total value of a and b.
   """
   return a - b
```

user:
Tests failed:
assert add(1, 2) == 3 # output: -1
assert add(1, 2) == 4 # output: -1

[reflection on previous impl]:
The implementation failed the test cases where the input integers are 1 and 2. The issue arises because the code does not add the two integers together, but instead subtracts the second integer from the first. To fix this issue, we should change the operator from `-` to `+` in the return statement. This will ensure that the function returns the correct output for the given input.

[improved impl]:
def add(a: int, b: int) -> int:
   """
   Given integers a and b, return the total value of a and b.
   """
   return a + b
'''

REFLECTION_PROMPT = """
[example]
Here is an example of debugging with reflection.
{debug_example}
[/example]

[context]
{context}

[previous impl]:
{previous_impl}

[instruction]
Analyze your previous code and error in [context] step by step, provide me with improved method and code. Remember to follow [context] requirement. Don't forget to write code for steps behind the error step.
Output a json following the format:
```json
{{
    "reflection": str = "Reflection on previous implementation",
    "improved_impl": str = "Refined code after reflection.",
}}
```
"""

CHECK_DATA_PROMPT = """
# Background
Check latest data info to guide subsequent tasks.

## Finished Tasks
```python
{code_written}
```end

# Task
Check code in finished tasks, print key variables to guide your following actions.
Specifically, if it is a data analysis or machine learning task, print the the latest column information using the following code, with DataFrame variable from 'Finished Tasks' in place of df:
```python
from metagpt.tools.libs.data_preprocess import get_column_info

column_info = get_column_info(df)
print("column_info")
print(column_info)
```end
Otherwise, print out any key variables you see fit. Return an empty string if you think there is no important data to check.

# Constraints:
- Your code is to be added to a new cell in jupyter.

# Instruction
Output code following the format:
```python
your code
```
"""

DATA_INFO = """
# Latest Data Info
Latest data info after previous tasks:
{info}
"""

TOOL_RECOMMENDATION_PROMPT = """
## User Requirement:
{current_task}

## Task
Recommend up to five tools from 'Available Tools' that can help solve the 'User Requirement'. 

## Available Tools:
{available_tools}

## Tool Selection and Instructions:
- Select tools most relevant to completing the 'User Requirement'.
- If you believe that no tools are suitable, indicate with an empty list.
- Only list the names of the tools, not the full schema of each tool.
- Ensure selected tools are listed in 'Available Tools'.
- Output a json list of tool names:
```json
["tool_name1", "tool_name2", ...]
```
"""

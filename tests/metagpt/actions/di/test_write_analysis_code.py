import pytest

from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_write_code_with_plan():
    write_code = WriteAnalysisCode()

    user_requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    plan_status = "\n## Finished Tasks\n### code\n```python\n\n```\n\n### execution result\n\n\n## Current Task\nLoad the sklearn Iris dataset and perform exploratory data analysis\n\n## Task Guidance\nWrite complete code for 'Current Task'. And avoid duplicating code from 'Finished Tasks', such as repeated import of packages, reading data, etc.\nSpecifically, \nThe current task is about exploratory data analysis, please note the following:\n- Distinguish column types with `select_dtypes` for tailored analysis and visualization, such as correlation.\n- Remember to `import numpy as np` before using Numpy functions.\n\n"

    code = await write_code.run(user_requirement=user_requirement, plan_status=plan_status)
    assert len(code) > 0
    assert "sklearn" in code


@pytest.mark.asyncio
async def test_write_code_with_tools():
    write_code = WriteAnalysisCode()

    user_requirement = "Preprocess sklearn Wine recognition dataset and train a model to predict wine class (20% as validation), and show validation accuracy."
    tool_info = """
    ## Capabilities
    - You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python class or function.
    - You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

    ## Available Tools:
    Each tool is described in JSON format. When you call a tool, import the tool from its path first.
    {'FillMissingValue': {'type': 'class', 'description': 'Completing missing values with simple strategies.', 'methods': {'__init__': {'type': 'function', 'description': 'Initialize self. ', 'signature': '(self, features: \'list\', strategy: "Literal[\'mean\', \'median\', \'most_frequent\', \'constant\']" = \'mean\', fill_value=None)', 'parameters': 'Args: features (list): Columns to be processed. strategy (Literal["mean", "median", "most_frequent", "constant"], optional): The imputation strategy, notice \'mean\' and \'median\' can only be used for numeric features. Defaults to \'mean\'. fill_value (int, optional): Fill_value is used to replace all occurrences of missing_values. Defaults to None.'}, 'fit': {'type': 'function', 'description': 'Fit a model to be used in subsequent transform. ', 'signature': "(self, df: 'pd.DataFrame')", 'parameters': 'Args: df (pd.DataFrame): The input DataFrame.'}, 'fit_transform': {'type': 'function', 'description': 'Fit and transform the input DataFrame. ', 'signature': "(self, df: 'pd.DataFrame') -> 'pd.DataFrame'", 'parameters': 'Args: df (pd.DataFrame): The input DataFrame. Returns: pd.DataFrame: The transformed DataFrame.'}, 'transform': {'type': 'function', 'description': 'Transform the input DataFrame with the fitted model. ', 'signature': "(self, df: 'pd.DataFrame') -> 'pd.DataFrame'", 'parameters': 'Args: df (pd.DataFrame): The input DataFrame. Returns: pd.DataFrame: The transformed DataFrame.'}}, 'tool_path': 'metagpt/tools/libs/data_preprocess.py'}
    """

    code = await write_code.run(user_requirement=user_requirement, tool_info=tool_info)
    assert len(code) > 0
    assert "metagpt.tools.libs" in code


@pytest.mark.asyncio
async def test_debug_with_reflection():
    user_requirement = "read a dataset test.csv and print its head"

    plan_status = """
    ## Finished Tasks
    ### code
    ```python
    ```

    ### execution result

    ## Current Task
    import pandas and load the dataset from 'test.csv'.

    ## Task Guidance
    Write complete code for 'Current Task'. And avoid duplicating code from 'Finished Tasks', such as repeated import of packages, reading data, etc.
    Specifically, 
    """

    wrong_code = """import pandas as pd\ndata = pd.read_excel('test.csv')\ndata"""  # use read_excel to read a csv
    error = """
    Traceback (most recent call last):
        File "<stdin>", line 2, in <module>
        File "/Users/gary/miniconda3/envs/py39_scratch/lib/python3.9/site-packages/pandas/io/excel/_base.py", line 478, in read_excel
            io = ExcelFile(io, storage_options=storage_options, engine=engine)
        File "/Users/gary/miniconda3/envs/py39_scratch/lib/python3.9/site-packages/pandas/io/excel/_base.py", line 1500, in __init__
            raise ValueError(
        ValueError: Excel file format cannot be determined, you must specify an engine manually.
    """
    working_memory = [
        Message(content=wrong_code, role="assistant"),
        Message(content=error, role="user"),
    ]
    new_code = await WriteAnalysisCode().run(
        user_requirement=user_requirement,
        plan_status=plan_status,
        working_memory=working_memory,
        use_reflection=True,
    )
    assert "read_csv" in new_code  # should correct read_excel to read_csv

from typing import Literal, Union

import pandas as pd

from metagpt.tools.tool_convert import (
    convert_code_to_tool_schema,
    convert_code_to_tool_schema_ast,
)


class DummyClass:
    """
    Completing missing values with simple strategies.
    """

    def __init__(self, features: list, strategy: str = "mean", fill_value=None):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
            strategy (str, optional): The imputation strategy, notice 'mean' and 'median' can only
                                      be used for numeric features. Enum: ['mean', 'median', 'most_frequent', 'constant']. Defaults to 'mean'.
            fill_value (int, optional): Fill_value is used to replace all occurrences of missing_values.
                                        Defaults to None.
        """
        pass

    def fit(self, df: pd.DataFrame):
        """
        Fit the FillMissingValue model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        pass

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        pass


def dummy_fn(
    df: pd.DataFrame,
    s: str,
    k: int = 5,
    type: Literal["a", "b", "c"] = "a",
    test_dict: dict[str, int] = None,
    test_union: Union[str, list[str]] = "",
) -> dict:
    """
    Analyzes a DataFrame and categorizes its columns based on data types.

    Args:
        df: The DataFrame to be analyzed.
            Another line for df.
        s (str): Some test string param.
            Another line for s.
        k (int, optional): Some test integer param. Defaults to 5.
        type (Literal["a", "b", "c"], optional): Some test type. Defaults to 'a'.
        more_args: will be omitted here for testing

    Returns:
        dict: A dictionary with four keys ('Category', 'Numeric', 'Datetime', 'Others').
              Each key corresponds to a list of column names belonging to that category.
    """
    pass


async def dummy_async_fn(df: pd.DataFrame) -> dict:
    """
    A dummy async function for test

    Args:
        df (pd.DataFrame): test args.

    Returns:
        dict: test returns.
    """
    pass


def test_convert_code_to_tool_schema_class():
    expected = {
        "type": "class",
        "description": "Completing missing values with simple strategies.",
        "methods": {
            "__init__": {
                "type": "function",
                "description": "Initialize self. ",
                "signature": "(self, features: list, strategy: str = 'mean', fill_value=None)",
                "parameters": "Args: features (list): Columns to be processed. strategy (str, optional): The imputation strategy, notice 'mean' and 'median' can only be used for numeric features. Enum: ['mean', 'median', 'most_frequent', 'constant']. Defaults to 'mean'. fill_value (int, optional): Fill_value is used to replace all occurrences of missing_values. Defaults to None.",
            },
            "fit": {
                "type": "function",
                "description": "Fit the FillMissingValue model. ",
                "signature": "(self, df: pandas.core.frame.DataFrame)",
                "parameters": "Args: df (pd.DataFrame): The input DataFrame.",
            },
            "transform": {
                "type": "function",
                "description": "Transform the input DataFrame with the fitted model. ",
                "signature": "(self, df: pandas.core.frame.DataFrame) -> pandas.core.frame.DataFrame",
                "parameters": "Args: df (pd.DataFrame): The input DataFrame. Returns: pd.DataFrame: The transformed DataFrame.",
            },
        },
    }
    schema = convert_code_to_tool_schema(DummyClass)
    assert schema == expected


def test_convert_code_to_tool_schema_function():
    expected = {
        "type": "function",
        "description": "Analyzes a DataFrame and categorizes its columns based on data types. ",
        "signature": "(df: pandas.core.frame.DataFrame, s: str, k: int = 5, type: Literal['a', 'b', 'c'] = 'a', test_dict: dict[str, int] = None, test_union: Union[str, list[str]] = '') -> dict",
        "parameters": "Args: df: The DataFrame to be analyzed. Another line for df. s (str): Some test string param. Another line for s. k (int, optional): Some test integer param. Defaults to 5. type (Literal[\"a\", \"b\", \"c\"], optional): Some test type. Defaults to 'a'. more_args: will be omitted here for testing Returns: dict: A dictionary with four keys ('Category', 'Numeric', 'Datetime', 'Others'). Each key corresponds to a list of column names belonging to that category.",
    }
    schema = convert_code_to_tool_schema(dummy_fn)
    assert schema == expected


def test_convert_code_to_tool_schema_async_function():
    schema = convert_code_to_tool_schema(dummy_async_fn)
    assert schema.get("type") == "async_function"


TEST_CODE_FILE_TEXT = '''
import pandas as pd  # imported obj should not be parsed
from some_module1 import some_imported_function, SomeImportedClass  # imported obj should not be parsed
from ..some_module2 import some_imported_function2  # relative import should not result in an error

class MyClass:
    """This is a MyClass docstring."""
    def __init__(self, arg1):
        """This is the constructor docstring."""
        self.arg1 = arg1

    def my_method(self, arg2: Union[list[str], str], arg3: pd.DataFrame, arg4: int = 1, arg5: Literal["a","b","c"] = "a") -> Tuple[int, str]:
        """
        This is a method docstring.
        
        Args:
            arg2 (Union[list[str], str]): A union of a list of strings and a string.
            ...
        
        Returns:
            Tuple[int, str]: A tuple of an integer and a string.
        """
        return self.arg4 + arg5
    
    async def my_async_method(self, some_arg) -> str:
        return "hi"
    
    def _private_method(self):  # private should not be parsed
        return "private"

def my_function(arg1, arg2) -> dict:
    """This is a function docstring."""
    return arg1 + arg2

def my_async_function(arg1, arg2) -> dict:
    return arg1 + arg2

def _private_function():  # private should not be parsed
    return "private"
'''


def test_convert_code_to_tool_schema_ast():
    expected = {
        "MyClass": {
            "type": "class",
            "description": "This is a MyClass docstring.",
            "methods": {
                "__init__": {
                    "type": "function",
                    "description": "This is the constructor docstring.",
                    "signature": "(self, arg1)",
                    "parameters": "",
                },
                "my_method": {
                    "type": "function",
                    "description": "This is a method docstring. ",
                    "signature": "(self, arg2: Union[list[str], str], arg3: pd.DataFrame, arg4: int = 1, arg5: Literal['a', 'b', 'c'] = 'a') -> Tuple[int, str]",
                    "parameters": "Args: arg2 (Union[list[str], str]): A union of a list of strings and a string. ... Returns: Tuple[int, str]: A tuple of an integer and a string.",
                },
                "my_async_method": {
                    "type": "async_function",
                    "description": "",
                    "signature": "(self, some_arg) -> str",
                    "parameters": "",
                },
            },
            "code": 'class MyClass:\n    """This is a MyClass docstring."""\n    def __init__(self, arg1):\n        """This is the constructor docstring."""\n        self.arg1 = arg1\n\n    def my_method(self, arg2: Union[list[str], str], arg3: pd.DataFrame, arg4: int = 1, arg5: Literal["a","b","c"] = "a") -> Tuple[int, str]:\n        """\n        This is a method docstring.\n        \n        Args:\n            arg2 (Union[list[str], str]): A union of a list of strings and a string.\n            ...\n        \n        Returns:\n            Tuple[int, str]: A tuple of an integer and a string.\n        """\n        return self.arg4 + arg5\n    \n    async def my_async_method(self, some_arg) -> str:\n        return "hi"\n    \n    def _private_method(self):  # private should not be parsed\n        return "private"',
        },
        "my_function": {
            "type": "function",
            "description": "This is a function docstring.",
            "signature": "(arg1, arg2) -> dict",
            "parameters": "",
            "code": 'def my_function(arg1, arg2) -> dict:\n    """This is a function docstring."""\n    return arg1 + arg2',
        },
        "my_async_function": {
            "type": "function",
            "description": "",
            "signature": "(arg1, arg2) -> dict",
            "parameters": "",
            "code": "def my_async_function(arg1, arg2) -> dict:\n    return arg1 + arg2",
        },
    }
    schemas = convert_code_to_tool_schema_ast(TEST_CODE_FILE_TEXT)
    assert schemas == expected

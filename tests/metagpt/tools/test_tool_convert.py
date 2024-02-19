import pandas as pd

from metagpt.tools.tool_convert import convert_code_to_tool_schema, docstring_to_schema


def test_docstring_to_schema():
    docstring = """
    Some test desc.

    Args:
        features (list): Columns to be processed.
        strategy (str, optional): The imputation strategy, notice 'mean' and 'median' can only be
                                used for numeric features. Enum: ['mean', 'median', 'most_frequent', 'constant']. Defaults to 'mean'.
        fill_value (int, optional): Fill_value is used to replace all occurrences of missing_values.
                                    Defaults to None.
    Returns:
        pd.DataFrame: The transformed DataFrame.
    """
    expected = {
        "description": "Some test desc.",
        "parameters": {
            "properties": {
                "features": {"type": "list", "description": "Columns to be processed."},
                "strategy": {
                    "type": "str",
                    "description": "The imputation strategy, notice 'mean' and 'median' can only be used for numeric features. Enum: ['mean', 'median', 'most_frequent', 'constant']. Defaults to 'mean'.",
                    "default": "'mean'",
                    "enum": ["'mean'", "'median'", "'most_frequent'", "'constant'"],
                },
                "fill_value": {
                    "type": "int",
                    "description": "Fill_value is used to replace all occurrences of missing_values. Defaults to None.",
                    "default": "None",
                },
            },
            "required": ["features"],
        },
        "returns": [{"type": "pd.DataFrame", "description": "The transformed DataFrame."}],
    }
    schema = docstring_to_schema(docstring)
    assert schema == expected


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


def dummy_fn(df: pd.DataFrame) -> dict:
    """
    Analyzes a DataFrame and categorizes its columns based on data types.

    Args:
        df (pd.DataFrame): The DataFrame to be analyzed.

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
                "description": "Initialize self.",
                "parameters": {
                    "properties": {
                        "features": {"type": "list", "description": "Columns to be processed."},
                        "strategy": {
                            "type": "str",
                            "description": "The imputation strategy, notice 'mean' and 'median' can only be used for numeric features. Enum: ['mean', 'median', 'most_frequent', 'constant']. Defaults to 'mean'.",
                            "default": "'mean'",
                            "enum": ["'mean'", "'median'", "'most_frequent'", "'constant'"],
                        },
                        "fill_value": {
                            "type": "int",
                            "description": "Fill_value is used to replace all occurrences of missing_values. Defaults to None.",
                            "default": "None",
                        },
                    },
                    "required": ["features"],
                },
            },
            "fit": {
                "type": "function",
                "description": "Fit the FillMissingValue model.",
                "parameters": {
                    "properties": {"df": {"type": "pd.DataFrame", "description": "The input DataFrame."}},
                    "required": ["df"],
                },
            },
            "transform": {
                "type": "function",
                "description": "Transform the input DataFrame with the fitted model.",
                "parameters": {
                    "properties": {"df": {"type": "pd.DataFrame", "description": "The input DataFrame."}},
                    "required": ["df"],
                },
                "returns": [{"type": "pd.DataFrame", "description": "The transformed DataFrame."}],
            },
        },
    }
    schema = convert_code_to_tool_schema(DummyClass)
    assert schema == expected


def test_convert_code_to_tool_schema_function():
    expected = {
        "type": "function",
        "description": "Analyzes a DataFrame and categorizes its columns based on data types.",
        "parameters": {
            "properties": {"df": {"type": "pd.DataFrame", "description": "The DataFrame to be analyzed."}},
            "required": ["df"],
        },
    }
    schema = convert_code_to_tool_schema(dummy_fn)
    assert schema == expected


def test_convert_code_to_tool_schema_async_function():
    schema = convert_code_to_tool_schema(dummy_async_fn)
    assert schema.get("type") == "async_function"

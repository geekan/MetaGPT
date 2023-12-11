
import pandas as pd

from metagpt.tools.functions.schemas.base import tool_field, ToolSchema


class FillMissingValue(ToolSchema):
    """Completing missing values with simple strategies"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")
    strategy: str = tool_field(description="the imputation strategy", default='mean')
    fill_value: int = tool_field(description="fill_value is used to replace all occurrences of missing_values", default=None)


# class LabelEncode(ToolSchema):
#     """Completing missing values with simple strategies"""
#     df: pd.DataFrame = tool_field(description="input dataframe")
#     features: list = tool_field(description="columns to be processed")


class SplitBins(ToolSchema):
    """Bin continuous data into intervals and return the bin identifier encoded as an integer value"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")
    strategy: str = tool_field(description="Strategy used to define the widths of the bins", default='quantile')


class MinMaxScale(ToolSchema):
    """Transform features by scaling each feature to a range, witch is (0, 1)"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


class StandardScale(ToolSchema):
    """Standardize features by removing the mean and scaling to unit variance"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


class LogTransform(ToolSchema):
    """Performs a logarithmic transformation on the specified columns"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


class MaxAbsScale(ToolSchema):
    """Scale each feature by its maximum absolute value"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


class RobustScale(ToolSchema):
    """Scale features using statistics that are robust to outliers, the quantile_range is (25.0, 75.0)"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


class OrdinalEncode(ToolSchema):
    """Encode categorical features as an integer array"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    features: list = tool_field(description="columns to be processed")


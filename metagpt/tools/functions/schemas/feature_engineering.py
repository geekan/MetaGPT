#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/17 10:34
# @Author  : lidanyang
# @File    : feature_engineering.py
# @Desc    : Schema for feature engineering functions
from typing import List

import pandas as pd

from metagpt.tools.functions.schemas.base import field, ToolSchema


class PolynomialExpansion(ToolSchema):
    """Generate polynomial and interaction features from selected columns, excluding the bias column."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    cols: list = field(description="Columns for polynomial expansion.")
    degree: int = field(description="Degree of polynomial features.", default=2)


class OneHotEncoding(ToolSchema):
    """Apply one-hot encoding to specified categorical columns in a DataFrame."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    cols: list = field(description="Categorical columns to be one-hot encoded.")


class FrequencyEncoding(ToolSchema):
    """Convert categorical columns to frequency encoding."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    cols: list = field(description="Categorical columns to be frequency encoded.")


class CatCross(ToolSchema):
    """Create pairwise crossed features from categorical columns, joining values with '_'."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    cols: list = field(description="Columns to be pairwise crossed.")
    max_cat_num: int = field(
        description="Maximum unique categories per crossed feature.", default=100
    )


class GroupStat(ToolSchema):
    """Perform aggregation operations on a specified column grouped by certain categories."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    group_col: str = field(description="Column used for grouping.")
    agg_col: str = field(description="Column on which aggregation is performed.")
    agg_funcs: list = field(
        description="""List of aggregation functions to apply, such as ['mean', 'std'].
                    Each function must be supported by pandas."""
    )


class ExtractTimeComps(ToolSchema):
    """Extract specific time components from a designated time column in a DataFrame."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    time_col: str = field(description="The name of the column containing time data.")
    time_comps: List[str] = field(
        description="""List of time components to extract.
        Each component must be in ['year', 'month', 'day', 'hour', 'dayofweek', 'is_weekend']."""
    )


class FeShiftByTime(ToolSchema):
    """Shift column values in a DataFrame based on specified time intervals."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    time_col: str = field(description="Column for time-based shifting.")
    group_col: str = field(description="Column for grouping before shifting.")
    shift_col: str = field(description="Column to shift.")
    periods: list = field(description="Time intervals for shifting.")
    freq: str = field(
        description="Frequency unit for time intervals (e.g., 'D', 'M').",
        enum=["D", "M", "Y", "W", "H"],
    )


class FeRollingByTime(ToolSchema):
    """Calculate rolling statistics for a DataFrame column over time intervals."""

    df: pd.DataFrame = field(description="DataFrame to process.")
    time_col: str = field(description="Column for time-based rolling.")
    group_col: str = field(description="Column for grouping before rolling.")
    rolling_col: str = field(description="Column for rolling calculations.")
    periods: list = field(description="Window sizes for rolling.")
    freq: str = field(
        description="Frequency unit for time windows (e.g., 'D', 'M').",
        enum=["D", "M", "Y", "W", "H"],
    )
    agg_funcs: list = field(
        description="""List of aggregation functions for rolling, like ['mean', 'std'].
        Each function must be in ['mean', 'std', 'min', 'max', 'median', 'sum', 'count']."""
    )

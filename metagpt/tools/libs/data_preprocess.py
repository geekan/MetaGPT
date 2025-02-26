from __future__ import annotations

import json
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import (
    LabelEncoder,
    MaxAbsScaler,
    MinMaxScaler,
    OneHotEncoder,
    OrdinalEncoder,
    RobustScaler,
    StandardScaler,
)

from metagpt.tools.tool_registry import register_tool

TAGS = ["data preprocessing", "machine learning"]


class MLProcess:
    def fit(self, df: pd.DataFrame):
        """
        Fit a model to be used in subsequent transform.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        raise NotImplementedError

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        raise NotImplementedError

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit and transform the input DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        self.fit(df)
        return self.transform(df)


class DataPreprocessTool(MLProcess):
    """
    Completing a data preprocessing operation.
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
        """
        self.features = features
        self.model = None  # to be filled by specific subclass Tool

    def fit(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return
        self.model.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(self.features) == 0:
            return df
        new_df = df.copy()
        new_df[self.features] = self.model.transform(new_df[self.features])
        return new_df


@register_tool(tags=TAGS)
class FillMissingValue(DataPreprocessTool):
    """
    Completing missing values with simple strategies.
    """

    def __init__(
        self, features: list, strategy: Literal["mean", "median", "most_frequent", "constant"] = "mean", fill_value=None
    ):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
            strategy (Literal["mean", "median", "most_frequent", "constant"], optional): The imputation strategy, notice 'mean' and 'median' can only
                                      be used for numeric features. Defaults to 'mean'.
            fill_value (int, optional): Fill_value is used to replace all occurrences of missing_values.
                                        Defaults to None.
        """
        self.features = features
        self.model = SimpleImputer(strategy=strategy, fill_value=fill_value)


@register_tool(tags=TAGS)
class MinMaxScale(DataPreprocessTool):
    """
    Transform features by scaling each feature to a range, which is (0, 1).
    """

    def __init__(self, features: list):
        self.features = features
        self.model = MinMaxScaler()


@register_tool(tags=TAGS)
class StandardScale(DataPreprocessTool):
    """
    Standardize features by removing the mean and scaling to unit variance.
    """

    def __init__(self, features: list):
        self.features = features
        self.model = StandardScaler()


@register_tool(tags=TAGS)
class MaxAbsScale(DataPreprocessTool):
    """
    Scale each feature by its maximum absolute value.
    """

    def __init__(self, features: list):
        self.features = features
        self.model = MaxAbsScaler()


@register_tool(tags=TAGS)
class RobustScale(DataPreprocessTool):
    """
    Apply the RobustScaler to scale features using statistics that are robust to outliers.
    """

    def __init__(self, features: list):
        self.features = features
        self.model = RobustScaler()


@register_tool(tags=TAGS)
class OrdinalEncode(DataPreprocessTool):
    """
    Encode categorical features as ordinal integers.
    """

    def __init__(self, features: list):
        self.features = features
        self.model = OrdinalEncoder()


@register_tool(tags=TAGS)
class OneHotEncode(DataPreprocessTool):
    """
    Apply one-hot encoding to specified categorical columns, the original columns will be dropped.
    """

    def __init__(self, features: list):
        self.features = features
        self.model = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        ts_data = self.model.transform(df[self.features])
        new_columns = self.model.get_feature_names_out(self.features)
        ts_data = pd.DataFrame(ts_data, columns=new_columns, index=df.index)
        new_df = df.drop(self.features, axis=1)
        new_df = pd.concat([new_df, ts_data], axis=1)
        return new_df


@register_tool(tags=TAGS)
class LabelEncode(DataPreprocessTool):
    """
    Apply label encoding to specified categorical columns in-place.
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Categorical columns to be label encoded.
        """
        self.features = features
        self.le_encoders = []

    def fit(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return
        for col in self.features:
            le = LabelEncoder().fit(df[col].astype(str).unique().tolist() + ["unknown"])
            self.le_encoders.append(le)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(self.features) == 0:
            return df
        new_df = df.copy()
        for i in range(len(self.features)):
            data_list = df[self.features[i]].astype(str).tolist()
            for unique_item in np.unique(df[self.features[i]].astype(str)):
                if unique_item not in self.le_encoders[i].classes_:
                    data_list = ["unknown" if x == unique_item else x for x in data_list]
            new_df[self.features[i]] = self.le_encoders[i].transform(data_list)
        return new_df


def get_column_info(df: pd.DataFrame) -> dict:
    """
    Analyzes a DataFrame and categorizes its columns based on data types.

    Args:
        df (pd.DataFrame): The DataFrame to be analyzed.

    Returns:
        dict: A dictionary with four keys ('Category', 'Numeric', 'Datetime', 'Others').
              Each key corresponds to a list of column names belonging to that category.
    """
    column_info = {
        "Category": [],
        "Numeric": [],
        "Datetime": [],
        "Others": [],
    }
    for col in df.columns:
        data_type = str(df[col].dtype).replace("dtype('", "").replace("')", "")
        if data_type.startswith("object"):
            column_info["Category"].append(col)
        elif data_type.startswith("int") or data_type.startswith("float"):
            column_info["Numeric"].append(col)
        elif data_type.startswith("datetime"):
            column_info["Datetime"].append(col)
        else:
            column_info["Others"].append(col)

    if len(json.dumps(column_info)) > 2000:
        column_info["Numeric"] = column_info["Numeric"][0:5] + ["Too many cols, omission here..."]
    return column_info

import json

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
from metagpt.tools.tool_types import ToolTypes

TOOL_TYPE = ToolTypes.DATA_PREPROCESS.type_name


class MLProcess(object):
    def fit(self, df):
        raise NotImplementedError

    def transform(self, df):
        raise NotImplementedError

    def fit_transform(self, df) -> pd.DataFrame:
        """
        Fit and transform the input DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        self.fit(df)
        return self.transform(df)


@register_tool(tool_type=TOOL_TYPE)
class FillMissingValue(MLProcess):
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
        self.features = features
        self.strategy = strategy
        self.fill_value = fill_value
        self.si = None

    def fit(self, df: pd.DataFrame):
        """
        Fit the FillMissingValue model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        if len(self.features) == 0:
            return
        self.si = SimpleImputer(strategy=self.strategy, fill_value=self.fill_value)
        self.si.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        if len(self.features) == 0:
            return df
        new_df = df.copy()
        new_df[self.features] = self.si.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class MinMaxScale(MLProcess):
    """
    Transform features by scaling each feature to a range, which is (0, 1).
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
        """
        self.features = features
        self.mms = None

    def fit(self, df: pd.DataFrame):
        """
        Fit the MinMaxScale model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        self.mms = MinMaxScaler()
        self.mms.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        new_df = df.copy()
        new_df[self.features] = self.mms.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class StandardScale(MLProcess):
    """
    Standardize features by removing the mean and scaling to unit variance.
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
        """
        self.features = features
        self.ss = None

    def fit(self, df: pd.DataFrame):
        """
        Fit the StandardScale model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        self.ss = StandardScaler()
        self.ss.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        new_df = df.copy()
        new_df[self.features] = self.ss.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class MaxAbsScale(MLProcess):
    """
    Scale each feature by its maximum absolute value.
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Columns to be processed.
        """
        self.features = features
        self.mas = None

    def fit(self, df: pd.DataFrame):
        """
        Fit the MaxAbsScale model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        self.mas = MaxAbsScaler()
        self.mas.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        new_df = df.copy()
        new_df[self.features] = self.mas.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class RobustScale(MLProcess):
    """
    Apply the RobustScaler to scale features using statistics that are robust to outliers.
    """

    def __init__(self, features: list):
        """
        Initialize the RobustScale instance with feature names.

        Args:
            features (list): List of feature names to be scaled.
        """
        self.features = features
        self.rs = None

    def fit(self, df: pd.DataFrame):
        """
        Compute the median and IQR for scaling.

        Args:
            df (pd.DataFrame): Dataframe containing the features.
        """
        self.rs = RobustScaler()
        self.rs.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        """
        Scale features using the previously computed median and IQR.

        Args:
            df (pd.DataFrame): Dataframe containing the features to be scaled.

        Returns:
            pd.DataFrame: A new dataframe with scaled features.
        """
        new_df = df.copy()
        new_df[self.features] = self.rs.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class OrdinalEncode(MLProcess):
    """
    Encode categorical features as ordinal integers.
    """

    def __init__(self, features: list):
        """
        Initialize the OrdinalEncode instance with feature names.

        Args:
            features (list): List of categorical feature names to be encoded.
        """
        self.features = features
        self.oe = None

    def fit(self, df: pd.DataFrame):
        """
        Learn the ordinal encodings for the features.

        Args:
            df (pd.DataFrame): Dataframe containing the categorical features.
        """
        self.oe = OrdinalEncoder()
        self.oe.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        """
        Convert the categorical features to ordinal integers.

        Args:
            df (pd.DataFrame): Dataframe containing the categorical features to be encoded.

        Returns:
            pd.DataFrame: A new dataframe with the encoded features.
        """
        new_df = df.copy()
        new_df[self.features] = self.oe.transform(new_df[self.features])
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class OneHotEncode(MLProcess):
    """
    Apply one-hot encoding to specified categorical columns, the original columns will be dropped.
    """

    def __init__(self, features: list):
        """
        Initialize self.

        Args:
            features (list): Categorical columns to be one-hot encoded and dropped.
        """
        self.features = features
        self.ohe = None

    def fit(self, df: pd.DataFrame):
        """
        Fit the OneHotEncoding model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        self.ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
        self.ohe.fit(df[self.features])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        ts_data = self.ohe.transform(df[self.features])
        new_columns = self.ohe.get_feature_names_out(self.features)
        ts_data = pd.DataFrame(ts_data, columns=new_columns, index=df.index)
        new_df = df.drop(self.features, axis=1)
        new_df = pd.concat([new_df, ts_data], axis=1)
        return new_df


@register_tool(tool_type=TOOL_TYPE)
class LabelEncode(MLProcess):
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
        """
        Fit the LabelEncode model.

        Args:
            df (pd.DataFrame): The input DataFrame.
        """
        if len(self.features) == 0:
            return
        for col in self.features:
            le = LabelEncoder().fit(df[col].astype(str).unique().tolist() + ["unknown"])
            self.le_encoders.append(le)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame with the fitted model.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
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

import json

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler

from metagpt.tools.functions.libs.base import MLProcess


class FillMissingValue(MLProcess):
    def __init__(self, features: list, strategy: str = 'mean', fill_value=None,):
        self.features = features
        self.strategy = strategy
        self.fill_value = fill_value
        self.si = None

    def fit(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return
        self.si = SimpleImputer(strategy=self.strategy, fill_value=self.fill_value)
        self.si.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return df
        df[self.features] = self.si.transform(df[self.features])
        return df


class MinMaxScale(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.mms = None

    def fit(self, df: pd.DataFrame):
        self.mms = MinMaxScaler()
        self.mms.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        df[self.features] = self.mms.transform(df[self.features])
        return df


class StandardScale(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.ss = None

    def fit(self, df: pd.DataFrame):
        self.ss = StandardScaler()
        self.ss.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        df[self.features] = self.ss.transform(df[self.features])
        return df


class MaxAbsScale(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.mas = None

    def fit(self, df: pd.DataFrame):
        self.mas = MaxAbsScaler()
        self.mas.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        df[self.features] = self.mas.transform(df[self.features])
        return df


class RobustScale(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.rs = None

    def fit(self, df: pd.DataFrame):
        self.rs = RobustScaler()
        self.rs.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        df[self.features] = self.rs.transform(df[self.features])
        return df


class OrdinalEncode(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.oe = None

    def fit(self, df: pd.DataFrame):
        self.oe = OrdinalEncoder()
        self.oe.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        df[self.features] = self.oe.transform(df[self.features])
        return df


class OneHotEncode(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.ohe = None

    def fit(self, df: pd.DataFrame):
        self.ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
        self.ohe.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
        ts_data = self.ohe.transform(df[self.features])
        new_columns = self.ohe.get_feature_names_out(self.features)
        ts_data = pd.DataFrame(ts_data, columns=new_columns, index=df.index)
        df.drop(self.features, axis=1, inplace=True)
        df = pd.concat([df, ts_data], axis=1)
        return df


class LabelEncode(MLProcess):
    def __init__(self, features: list,):
        self.features = features
        self.le_encoders = []

    def fit(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return
        for col in self.features:
            le = LabelEncoder().fit(df[col].astype(str).unique().tolist() + ['unknown'])
            self.le_encoders.append(le)

    def transform(self, df: pd.DataFrame):
        if len(self.features) == 0:
            return df
        for i in range(len(self.features)):
            data_list = df[self.features[i]].astype(str).tolist()
            for unique_item in np.unique(df[self.features[i]].astype(str)):
                if unique_item not in self.le_encoders[i].classes_:
                    data_list = ['unknown' if x == unique_item else x for x in data_list]
            df[self.features[i]] = self.le_encoders[i].transform(data_list)
        return df


def get_column_info(df: pd.DataFrame) -> dict:
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
        column_info['Numeric'] = column_info['Numeric'][0:5] + ['Too many cols, omission here...']
    return column_info

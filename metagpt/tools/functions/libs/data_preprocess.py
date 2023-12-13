import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler

from metagpt.tools.functions.libs.base import MLProcess
from metagpt.tools.functions.schemas.data_preprocess import *


class FillMissingValue(MLProcess):
    def __init__(self, features: list, strategy: str = 'mean', fill_value=None,):
        self.features = features
        self.strategy = strategy
        self.fill_value = fill_value
        self.si = None

    def fit(self, df: pd.DataFrame):
        self.si = SimpleImputer(strategy=self.strategy, fill_value=self.fill_value)
        self.si.fit(df[self.features])

    def transform(self, df: pd.DataFrame):
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
        for col in self.features:
            le = LabelEncoder().fit(df[col].astype(str).unique().tolist() + ['unknown'])
            self.le_encoders.append(le)

    def transform(self, df: pd.DataFrame):
        for i in range(len(self.features)):
            data_list = df[self.features[i]].astype(str).tolist()
            for unique_item in np.unique(df[self.features[i]].astype(str)):
                if unique_item not in self.le_encoders[i].classes_:
                    data_list = ['unknown' if x == unique_item else x for x in data_list]
            df[self.features[i]] = self.le_encoders[i].transform(data_list)
        return df


def get_column_info(df: pd.DataFrame) -> dict:
    data = []
    for i in df.columns:
        nan_freq = float("%.2g" % (df[i].isna().mean() * 100))
        n_unique = df[i].nunique()
        data.append([i, df[i].dtype, nan_freq, n_unique])

    samples = pd.DataFrame(
        data,
        columns=["Column_name", "Data_type", "NaN_Frequency(%)", "N_unique"],
    )
    return samples.to_dict(orient='list')
#
#
# if __name__ == '__main__':
#     def run():
#         V = {
#             'a': [-1, 2, 3, 6, 5, 4],
#             'b': [1.1, 2.2, 3.3, 6.6, 5.5, 4.4],
#             'c': ['aa', 'bb', 'cc', 'dd', 'ee', 'ff'],
#             'd': [1, None, 3, None, 5, 4],
#             'e': [1.1, np.NAN, 3.3, None, 5.5, 4.4],
#             'f': ['aa', np.NAN, 'cc', None, '', 'ff'],
#
#         }
#
#         df = pd.DataFrame(V)
#         print(df.dtypes)
#
#         numeric_features = ['a', 'b', 'd', 'e']
#         numeric_features_wo_miss = ['a', 'b', ]
#         categorial_features = ['c', 'f']
#
#         df_ = fill_missing_value(df.copy(), numeric_features)
#         print(df_)
#         df_ = fill_missing_value(df.copy(), categorial_features, strategy='constant', fill_value='hehe')
#         print(df_)
#
#         df_ = fill_missing_value(df.copy(), numeric_features, strategy='constant', fill_value=999)
#         print(df_)
#
#         # df_ = label_encode(df.copy(), numeric_features + categorial_features, )
#         # print(df_)
#
#         df_ = split_bins(df.copy(), numeric_features_wo_miss, strategy='quantile')
#         print(df_)
#
#         df_ = min_max_scale(df.copy(), numeric_features, )
#         print(df_)
#
#         df_ = standard_scale(df.copy(), numeric_features, )
#         print(df_)
#
#         df_ = log_transform(df.copy(), numeric_features, )
#         print(df_)
#
#         df_ = max_abs_scale(df.copy(), numeric_features, )
#         print(df_)
#
#         df_ = robust_scale(df.copy(), numeric_features, )
#         print(df_)
#     run()
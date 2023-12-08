import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler

from metagpt.tools.functions import registry
from metagpt.tools.functions.schemas.data_preprocess import *


@registry.register("data_preprocess", FillMissingValue)
def fill_missing_value(df: pd.DataFrame, features: list, strategy: str = 'mean', fill_value=None,):
    df[features] = SimpleImputer(strategy=strategy, fill_value=fill_value).fit_transform(df[features])
    return df


@registry.register("data_preprocess", SplitBins)
def split_bins(df: pd.DataFrame, features: list, strategy: str = 'quantile',):
    df[features] = KBinsDiscretizer(strategy=strategy, encode='ordinal').fit_transform(df[features])
    return df


@registry.register("data_preprocess", MinMaxScale)
def min_max_scale(df: pd.DataFrame, features: list, ):
    df[features] = MinMaxScaler().fit_transform(df[features])
    return df


@registry.register("data_preprocess", StandardScale)
def standard_scale(df: pd.DataFrame, features: list, ):
    df[features] = StandardScaler().fit_transform(df[features])
    return df


@registry.register("data_preprocess", LogTransform)
def log_transform(df: pd.DataFrame, features: list, ):
    for col in features:
        if df[col].min() <= 0:
            df[col] = df[col] - df[col].min() + 2
        df[col] = np.log(df[col])
    return df


@registry.register("data_preprocess", MaxAbsScale)
def max_abs_scale(df: pd.DataFrame, features: list, ):
    df[features] = MaxAbsScaler().fit_transform(df[features])
    return df


@registry.register("data_preprocess", RobustScale)
def robust_scale(df: pd.DataFrame, features: list, ):
    df[features] = RobustScaler().fit_transform(df[features])
    return df


@registry.register("data_preprocess", OrdinalEncode)
def ordinal_encode(df: pd.DataFrame, features: list,):
    df[features] = OrdinalEncoder().fit_transform(df[features])
    return df


@registry.register("data_preprocess", OneHotEncoding)
def one_hot_encoding(df, cols):
    enc = OneHotEncoder(handle_unknown="ignore", sparse=False)
    ts_data = enc.fit_transform(df[cols])
    new_columns = enc.get_feature_names_out(cols)
    ts_data = pd.DataFrame(ts_data, columns=new_columns, index=df.index)
    df.drop(cols, axis=1, inplace=True)
    df = pd.concat([df, ts_data], axis=1)
    return df


if __name__ == '__main__':
    def run():
        V = {
            'a': [-1, 2, 3, 6, 5, 4],
            'b': [1.1, 2.2, 3.3, 6.6, 5.5, 4.4],
            'c': ['aa', 'bb', 'cc', 'dd', 'ee', 'ff'],
            'd': [1, None, 3, None, 5, 4],
            'e': [1.1, np.NAN, 3.3, None, 5.5, 4.4],
            'f': ['aa', np.NAN, 'cc', None, '', 'ff'],

        }

        df = pd.DataFrame(V)
        print(df.dtypes)

        numeric_features = ['a', 'b', 'd', 'e']
        numeric_features_wo_miss = ['a', 'b', ]
        categorial_features = ['c', 'f']

        df_ = fill_missing_value(df.copy(), numeric_features)
        print(df_)
        df_ = fill_missing_value(df.copy(), categorial_features, strategy='constant', fill_value='hehe')
        print(df_)

        df_ = fill_missing_value(df.copy(), numeric_features, strategy='constant', fill_value=999)
        print(df_)

        # df_ = label_encode(df.copy(), numeric_features + categorial_features, )
        # print(df_)

        df_ = split_bins(df.copy(), numeric_features_wo_miss, strategy='quantile')
        print(df_)

        df_ = min_max_scale(df.copy(), numeric_features, )
        print(df_)

        df_ = standard_scale(df.copy(), numeric_features, )
        print(df_)

        df_ = log_transform(df.copy(), numeric_features, )
        print(df_)

        df_ = max_abs_scale(df.copy(), numeric_features, )
        print(df_)

        df_ = robust_scale(df.copy(), numeric_features, )
        print(df_)
    run()
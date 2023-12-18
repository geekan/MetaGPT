#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/17 10:33
# @Author  : lidanyang
# @File    : feature_engineering.py
# @Desc    : Feature Engineering Tools
import itertools

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from joblib import Parallel, delayed
from pandas.api.types import is_numeric_dtype
from pandas.core.dtypes.common import is_object_dtype
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures, KBinsDiscretizer

from metagpt.tools.functions.libs.base import MLProcess


class PolynomialExpansion(MLProcess):
    def __init__(self, cols: list, degree: int = 2):
        self.cols = cols
        self.degree = degree
        self.poly = PolynomialFeatures(degree=degree, include_bias=False)

    def fit(self, df: pd.DataFrame):
        self.poly.fit(df[self.cols].fillna(0))

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        ts_data = self.poly.transform(df[self.cols].fillna(0))
        column_name = self.poly.get_feature_names_out(self.cols)
        ts_data = pd.DataFrame(ts_data, index=df.index, columns=column_name)
        df.drop(self.cols, axis=1, inplace=True)
        df = pd.concat([df, ts_data], axis=1)
        return df


class CatCount(MLProcess):
    def __init__(self, col: str):
        self.col = col
        self.encoder_dict = None

    def fit(self, df: pd.DataFrame):
        self.encoder_dict = df[self.col].value_counts().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df[f"{self.col}_cnt"] = df[self.col].map(self.encoder_dict)
        return df


class TargetMeanEncoder(MLProcess):
    def __init__(self, col: str, label: str):
        self.col = col
        self.label = label
        self.encoder_dict = None

    def fit(self, df: pd.DataFrame):
        self.encoder_dict = df.groupby(self.col)[self.label].mean().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df[f"{self.col}_target_mean"] = df[self.col].map(self.encoder_dict)
        return df


class KFoldTargetMeanEncoder(MLProcess):
    def __init__(self, col: str, label: str, n_splits: int = 5, random_state: int = 2021):
        self.col = col
        self.label = label
        self.n_splits = n_splits
        self.random_state = random_state
        self.encoder_dict = None

    def fit(self, df: pd.DataFrame):
        tmp = df.copy()
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)

        global_mean = tmp[self.label].mean()
        col_name = f"{self.col}_kf_target_mean"
        for trn_idx, val_idx in kf.split(tmp, tmp[self.label]):
            _trn, _val = tmp.iloc[trn_idx], tmp.iloc[val_idx]
            tmp.loc[tmp.index[val_idx], col_name] = _val[self.col].map(
                _trn.groupby(self.col)[self.label].mean()
            )
        tmp[col_name].fillna(global_mean, inplace=True)
        self.encoder_dict = tmp.groupby(self.col)[col_name].mean().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df[f"{self.col}_kf_target_mean"] = df[self.col].map(self.encoder_dict)
        return df


class CatCross(MLProcess):
    def __init__(self, cols: list, max_cat_num: int = 100):
        self.cols = cols
        self.max_cat_num = max_cat_num
        self.combs = []
        self.combs_map = {}

    @staticmethod
    def cross_two(comb, df):
        new_col = f'{comb[0]}_{comb[1]}'
        new_col_combs = list(itertools.product(df[comb[0]].unique(), df[comb[1]].unique()))
        ll = list(range(len(new_col_combs)))
        comb_map = dict(zip(new_col_combs, ll))
        return new_col, comb_map

    def fit(self, df: pd.DataFrame):
        for col in self.cols:
            if df[col].nunique() > self.max_cat_num:
                self.cols.remove(col)
        self.combs = list(itertools.combinations(self.cols, 2))
        res = Parallel(n_jobs=4, require='sharedmem')(
            delayed(self.cross_two)(comb, df) for comb in self.combs)
        self.combs_map = dict(res)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for comb in self.combs:
            new_col = f'{comb[0]}_{comb[1]}'
            _map = self.combs_map[new_col]
            df[new_col] = pd.Series(zip(df[comb[0]], df[comb[1]])).map(_map)
            # set the unknown value to a new number
            df[new_col].fillna(max(_map.values()) + 1, inplace=True)
            df[new_col] = df[new_col].astype(int)
        return df


class GroupStat(MLProcess):
    def __init__(self, group_col: str, agg_col: str, agg_funcs: list):
        self.group_col = group_col
        self.agg_col = agg_col
        self.agg_funcs = agg_funcs
        self.group_df = None

    def fit(self, df: pd.DataFrame):
        group_df = df.groupby(self.group_col)[self.agg_col].agg(self.agg_funcs).reset_index()
        group_df.columns = [self.group_col] + [
            f"{self.agg_col}_{agg_func}_by_{self.group_col}" for agg_func in self.agg_funcs
        ]
        self.group_df = group_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.merge(self.group_df, on=self.group_col, how="left")
        return df


class SplitBins(MLProcess):
    def __init__(self, cols: str, strategy: str = 'quantile'):
        self.cols = cols
        self.strategy = strategy
        self.encoder = None

    def fit(self, df: pd.DataFrame):
        self.encoder = KBinsDiscretizer(strategy=self.strategy, encode='ordinal')
        self.encoder.fit(df[self.cols].fillna(0))

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.cols] = self.encoder.transform(df[self.cols].fillna(0))
        return df

# @registry.register("feature_engineering", ExtractTimeComps)
# def extract_time_comps(df, time_col, time_comps):
#     time_s = pd.to_datetime(df[time_col], errors="coerce")
#     time_comps_df = pd.DataFrame()
#
#     if "year" in time_comps:
#         time_comps_df["year"] = time_s.dt.year
#     if "month" in time_comps:
#         time_comps_df["month"] = time_s.dt.month
#     if "day" in time_comps:
#         time_comps_df["day"] = time_s.dt.day
#     if "hour" in time_comps:
#         time_comps_df["hour"] = time_s.dt.hour
#     if "dayofweek" in time_comps:
#         time_comps_df["dayofweek"] = time_s.dt.dayofweek + 1
#     if "is_weekend" in time_comps:
#         time_comps_df["is_weekend"] = time_s.dt.dayofweek.isin([5, 6]).astype(int)
#     df = pd.concat([df, time_comps_df], axis=1)
#     return df
#
#
# @registry.register("feature_engineering", FeShiftByTime)
# def fe_shift_by_time(df, time_col, group_col, shift_col, periods, freq):
#     df[time_col] = pd.to_datetime(df[time_col])
#
#     def shift_datetime(date, offset, unit):
#         if unit in ["year", "y", "Y"]:
#             return date + relativedelta(years=offset)
#         elif unit in ["month", "m", "M"]:
#             return date + relativedelta(months=offset)
#         elif unit in ["day", "d", "D"]:
#             return date + relativedelta(days=offset)
#         elif unit in ["week", "w", "W"]:
#             return date + relativedelta(weeks=offset)
#         elif unit in ["hour", "h", "H"]:
#             return date + relativedelta(hours=offset)
#         else:
#             return date
#
#     def shift_by_time_on_key(
#         inner_df, time_col, group_col, shift_col, offset, unit, col_name
#     ):
#         inner_df = inner_df.drop_duplicates()
#         inner_df[time_col] = inner_df[time_col].map(
#             lambda x: shift_datetime(x, offset, unit)
#         )
#         inner_df = inner_df.groupby([time_col, group_col], as_index=False)[
#             shift_col
#         ].mean()
#         inner_df.rename(columns={shift_col: col_name}, inplace=True)
#         return inner_df
#
#     shift_df = df[[time_col, group_col, shift_col]].copy()
#     for period in periods:
#         new_col_name = f"{group_col}_{shift_col}_lag_{period}_{freq}"
#         tmp = shift_by_time_on_key(
#             shift_df, time_col, group_col, shift_col, period, freq, new_col_name
#         )
#         df = df.merge(tmp, on=[time_col, group_col], how="left")
#
#     return df
#
#
# @registry.register("feature_engineering", FeRollingByTime)
# def fe_rolling_by_time(df, time_col, group_col, rolling_col, periods, freq, agg_funcs):
#     df[time_col] = pd.to_datetime(df[time_col])
#
#     def rolling_by_time_on_key(inner_df, offset, unit, agg_func, col_name):
#         time_freq = {
#             "Y": [365 * offset, "D"],
#             "M": [30 * offset, "D"],
#             "D": [offset, "D"],
#             "W": [7 * offset, "D"],
#             "H": [offset, "h"],
#         }
#
#         if agg_func not in ["mean", "std", "max", "min", "median", "sum", "count"]:
#             raise ValueError(f"Invalid agg function: {agg_func}")
#
#         rolling_feat = inner_df.rolling(
#             f"{time_freq[unit][0]}{time_freq[unit][1]}", closed="left"
#         )
#         rolling_feat = getattr(rolling_feat, agg_func)()
#         depth = df.columns.nlevels
#         rolling_feat = rolling_feat.stack(list(range(depth)))
#         rolling_feat.name = col_name
#         return rolling_feat
#
#     rolling_df = df[[time_col, group_col, rolling_col]].copy()
#     for period in periods:
#         for func in agg_funcs:
#             new_col_name = f"{group_col}_{rolling_col}_rolling_{period}_{freq}_{func}"
#             tmp = pd.pivot_table(
#                 rolling_df,
#                 index=time_col,
#                 values=rolling_col,
#                 columns=group_col,
#             )
#             tmp = rolling_by_time_on_key(tmp, period, freq, func, new_col_name)
#             df = df.merge(tmp, on=[time_col, group_col], how="left")
#
#     return df


class GeneralSelection(MLProcess):
    def __init__(self, label_col: str):
        self.label_col = label_col
        self.feats = []

    def fit(self, df: pd.DataFrame):
        feats = [f for f in df.columns if f != self.label_col]
        for col in df.columns:
            if df[col].isnull().sum() / df.shape[0] == 1:
                feats.remove(col)

            if df[col].nunique() == 1:
                feats.remove(col)

            if (
                df.loc[df[col] == np.inf].shape[0] != 0
                or df.loc[df[col] == np.inf].shape[0] != 0
            ):
                feats.remove(col)

            if is_object_dtype(df[col]) and df[col].nunique() == df.shape[0]:
                feats.remove(col)

        self.feats = feats

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[self.feats + [self.label_col]]
        return df

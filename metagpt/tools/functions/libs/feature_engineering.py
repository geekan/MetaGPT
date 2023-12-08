#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/17 10:33
# @Author  : lidanyang
# @File    : feature_engineering.py
# @Desc    : Feature Engineering Functions
import itertools

from dateutil.relativedelta import relativedelta
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from metagpt.tools.functions import registry
from metagpt.tools.functions.schemas.feature_engineering import *


@registry.register("feature_engineering", PolynomialExpansion)
def polynomial_expansion(df, cols, degree=2):
    for col in cols:
        if not is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' must be numeric.")

    poly = PolynomialFeatures(degree=degree, include_bias=False)
    ts_data = poly.fit_transform(df[cols].fillna(0))
    new_columns = poly.get_feature_names_out(cols)
    ts_data = pd.DataFrame(ts_data, columns=new_columns, index=df.index)
    ts_data = ts_data.drop(cols, axis=1)
    df = pd.concat([df, ts_data], axis=1)
    return df


@registry.register("feature_engineering", FrequencyEncoding)
def frequency_encoding(df, cols):
    for col in cols:
        encoder_dict = df[col].value_counts().to_dict()
        df[f"{col}_cnt"] = df[col].map(encoder_dict)
    return df


@registry.register("feature_engineering", TargetMeanEncoder)
def target_mean_encoder(df, col, label):
    encoder_dict = df.groupby(col)[label].mean().to_dict()
    df[f"{col}_target_mean"] = df[col].map(encoder_dict)
    return df


@registry.register("feature_engineering", KFoldTargetMeanEncoder)
def k_fold_target_mean_encoder(df, col, label, n_splits=5, random_state=2021):
    tmp = df.copy()
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    global_mean = tmp[label].mean()
    col_name = f"{col}_kf_target_mean"
    for trn_idx, val_idx in kf.split(tmp, tmp[label]):
        _trn, _val = tmp.iloc[trn_idx], tmp.iloc[val_idx]
        tmp.loc[tmp.index[val_idx], col_name] = _val[col].map(
            _trn.groupby(col)[label].mean()
        )
    tmp[col_name].fillna(global_mean, inplace=True)
    encoder_dict = tmp.groupby(col)[col_name].mean().to_dict()
    df[f"{col}_kf_target_mean"] = df[col].map(encoder_dict)
    return df


@registry.register("feature_engineering", CatCross)
def cat_cross(df, cols, max_cat_num=100):
    for col in cols:
        if df[col].nunique() > max_cat_num:
            cols.remove(col)

    for col1, col2 in itertools.combinations(cols, 2):
        cross_col = f"{col1}_cross_{col2}"
        crossed = df[col1].astype(str) + "_" + df[col2].astype(str)
        df[cross_col] = crossed.astype('category').cat.codes
    return df


@registry.register("feature_engineering", GroupStat)
def group_stat(df, group_col, agg_col, agg_funcs):
    group_df = df.groupby(group_col)[agg_col].agg(agg_funcs).reset_index()
    group_df.columns = group_col + [
        f"{agg_col}_{agg_func}_by_{group_col}" for agg_func in agg_funcs
    ]
    df = df.merge(group_df, on=group_col, how="left")
    return df


@registry.register("feature_engineering", ExtractTimeComps)
def extract_time_comps(df, time_col, time_comps):
    time_s = pd.to_datetime(df[time_col], errors="coerce")
    time_comps_df = pd.DataFrame()

    if "year" in time_comps:
        time_comps_df["year"] = time_s.dt.year
    if "month" in time_comps:
        time_comps_df["month"] = time_s.dt.month
    if "day" in time_comps:
        time_comps_df["day"] = time_s.dt.day
    if "hour" in time_comps:
        time_comps_df["hour"] = time_s.dt.hour
    if "dayofweek" in time_comps:
        time_comps_df["dayofweek"] = time_s.dt.dayofweek + 1
    if "is_weekend" in time_comps:
        time_comps_df["is_weekend"] = time_s.dt.dayofweek.isin([5, 6]).astype(int)
    df = pd.concat([df, time_comps_df], axis=1)
    return df


@registry.register("feature_engineering", FeShiftByTime)
def fe_shift_by_time(df, time_col, group_col, shift_col, periods, freq):
    df[time_col] = pd.to_datetime(df[time_col])

    def shift_datetime(date, offset, unit):
        if unit in ["year", "y", "Y"]:
            return date + relativedelta(years=offset)
        elif unit in ["month", "m", "M"]:
            return date + relativedelta(months=offset)
        elif unit in ["day", "d", "D"]:
            return date + relativedelta(days=offset)
        elif unit in ["week", "w", "W"]:
            return date + relativedelta(weeks=offset)
        elif unit in ["hour", "h", "H"]:
            return date + relativedelta(hours=offset)
        else:
            return date

    def shift_by_time_on_key(
        inner_df, time_col, group_col, shift_col, offset, unit, col_name
    ):
        inner_df = inner_df.drop_duplicates()
        inner_df[time_col] = inner_df[time_col].map(
            lambda x: shift_datetime(x, offset, unit)
        )
        inner_df = inner_df.groupby([time_col, group_col], as_index=False)[
            shift_col
        ].mean()
        inner_df.rename(columns={shift_col: col_name}, inplace=True)
        return inner_df

    shift_df = df[[time_col, group_col, shift_col]].copy()
    for period in periods:
        new_col_name = f"{group_col}_{shift_col}_lag_{period}_{freq}"
        tmp = shift_by_time_on_key(
            shift_df, time_col, group_col, shift_col, period, freq, new_col_name
        )
        df = df.merge(tmp, on=[time_col, group_col], how="left")

    return df


@registry.register("feature_engineering", FeRollingByTime)
def fe_rolling_by_time(df, time_col, group_col, rolling_col, periods, freq, agg_funcs):
    df[time_col] = pd.to_datetime(df[time_col])

    def rolling_by_time_on_key(inner_df, offset, unit, agg_func, col_name):
        time_freq = {
            "Y": [365 * offset, "D"],
            "M": [30 * offset, "D"],
            "D": [offset, "D"],
            "W": [7 * offset, "D"],
            "H": [offset, "h"],
        }

        if agg_func not in ["mean", "std", "max", "min", "median", "sum", "count"]:
            raise ValueError(f"Invalid agg function: {agg_func}")

        rolling_feat = inner_df.rolling(
            f"{time_freq[unit][0]}{time_freq[unit][1]}", closed="left"
        )
        rolling_feat = getattr(rolling_feat, agg_func)()
        depth = df.columns.nlevels
        rolling_feat = rolling_feat.stack(list(range(depth)))
        rolling_feat.name = col_name
        return rolling_feat

    rolling_df = df[[time_col, group_col, rolling_col]].copy()
    for period in periods:
        for func in agg_funcs:
            new_col_name = f"{group_col}_{rolling_col}_rolling_{period}_{freq}_{func}"
            tmp = pd.pivot_table(
                rolling_df,
                index=time_col,
                values=rolling_col,
                columns=group_col,
            )
            tmp = rolling_by_time_on_key(tmp, period, freq, func, new_col_name)
            df = df.merge(tmp, on=[time_col, group_col], how="left")

    return df

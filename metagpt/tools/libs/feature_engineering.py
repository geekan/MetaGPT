#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/17 10:33
# @Author  : lidanyang
# @File    : feature_engineering.py
# @Desc    : Feature Engineering Tools
from __future__ import annotations

import itertools

# import lightgbm as lgb
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from pandas.core.dtypes.common import is_object_dtype
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import KFold
from sklearn.preprocessing import KBinsDiscretizer, PolynomialFeatures

from metagpt.tools.libs.data_preprocess import MLProcess
from metagpt.tools.tool_registry import register_tool

TAGS = ["feature engineering", "machine learning"]


@register_tool(tags=TAGS)
class PolynomialExpansion(MLProcess):
    """
    Add polynomial and interaction features from selected numeric columns to input DataFrame.
    """

    def __init__(self, cols: list, label_col: str, degree: int = 2):
        """
        Initialize self.

        Args:
            cols (list): Columns for polynomial expansion.
            label_col (str): Label column name.
            degree (int, optional): The degree of the polynomial features. Defaults to 2.
        """
        self.cols = cols
        self.degree = degree
        self.label_col = label_col
        if self.label_col in self.cols:
            self.cols.remove(self.label_col)
        self.poly = PolynomialFeatures(degree=degree, include_bias=False)

    def fit(self, df: pd.DataFrame):
        if len(self.cols) == 0:
            return
        if len(self.cols) > 10:
            corr = df[self.cols + [self.label_col]].corr()
            corr = corr[self.label_col].abs().sort_values(ascending=False)
            self.cols = corr.index.tolist()[1:11]

        self.poly.fit(df[self.cols].fillna(0))

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(self.cols) == 0:
            return df
        ts_data = self.poly.transform(df[self.cols].fillna(0))
        column_name = self.poly.get_feature_names_out(self.cols)
        ts_data = pd.DataFrame(ts_data, index=df.index, columns=column_name)
        new_df = df.drop(self.cols, axis=1)
        new_df = pd.concat([new_df, ts_data], axis=1)
        return new_df


@register_tool(tags=TAGS)
class CatCount(MLProcess):
    """
    Add value counts of a categorical column as new feature.
    """

    def __init__(self, col: str):
        """
        Initialize self.

        Args:
            col (str): Column for value counts.
        """
        self.col = col
        self.encoder_dict = None

    def fit(self, df: pd.DataFrame):
        self.encoder_dict = df[self.col].value_counts().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()
        new_df[f"{self.col}_cnt"] = new_df[self.col].map(self.encoder_dict)
        return new_df


@register_tool(tags=TAGS)
class TargetMeanEncoder(MLProcess):
    """
    Encode a categorical column by the mean of the label column, and adds the result as a new feature.
    """

    def __init__(self, col: str, label: str):
        """
        Initialize self.

        Args:
            col (str): Column to be mean encoded.
            label (str): Predicted label column.
        """
        self.col = col
        self.label = label
        self.encoder_dict = None

    def fit(self, df: pd.DataFrame):
        self.encoder_dict = df.groupby(self.col)[self.label].mean().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()
        new_df[f"{self.col}_target_mean"] = new_df[self.col].map(self.encoder_dict)
        return new_df


@register_tool(tags=TAGS)
class KFoldTargetMeanEncoder(MLProcess):
    """
    Add a new feature to the DataFrame by k-fold mean encoding of a categorical column using the label column.
    """

    def __init__(self, col: str, label: str, n_splits: int = 5, random_state: int = 2021):
        """
        Initialize self.

        Args:
            col (str): Column to be k-fold mean encoded.
            label (str): Predicted label column.
            n_splits (int, optional): Number of splits for K-fold. Defaults to 5.
            random_state (int, optional): Random seed. Defaults to 2021.
        """
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
            tmp.loc[tmp.index[val_idx], col_name] = _val[self.col].map(_trn.groupby(self.col)[self.label].mean())
        tmp[col_name].fillna(global_mean, inplace=True)
        self.encoder_dict = tmp.groupby(self.col)[col_name].mean().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()
        new_df[f"{self.col}_kf_target_mean"] = new_df[self.col].map(self.encoder_dict)
        return new_df


@register_tool(tags=TAGS)
class CatCross(MLProcess):
    """
    Add pairwise crossed features and convert them to numerical features.
    """

    def __init__(self, cols: list, max_cat_num: int = 100):
        """
        Initialize self.

        Args:
            cols (list): Columns to be pairwise crossed, at least 2 columns.
            max_cat_num (int, optional): Maximum unique categories per crossed feature. Defaults to 100.
        """
        self.cols = cols
        self.max_cat_num = max_cat_num
        self.combs = []
        self.combs_map = {}

    @staticmethod
    def _cross_two(comb, df):
        """
        Cross two columns and convert them to numerical features.

        Args:
            comb (tuple): The pair of columns to be crossed.
            df (pd.DataFrame): The input DataFrame.

        Returns:
            tuple: The new column name and the crossed feature map.
        """
        new_col = f"{comb[0]}_{comb[1]}"
        new_col_combs = list(itertools.product(df[comb[0]].unique(), df[comb[1]].unique()))
        ll = list(range(len(new_col_combs)))
        comb_map = dict(zip(new_col_combs, ll))
        return new_col, comb_map

    def fit(self, df: pd.DataFrame):
        for col in self.cols:
            if df[col].nunique() > self.max_cat_num:
                self.cols.remove(col)
        self.combs = list(itertools.combinations(self.cols, 2))
        res = Parallel(n_jobs=4, require="sharedmem")(delayed(self._cross_two)(comb, df) for comb in self.combs)
        self.combs_map = dict(res)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()
        for comb in self.combs:
            new_col = f"{comb[0]}_{comb[1]}"
            _map = self.combs_map[new_col]
            new_df[new_col] = pd.Series(zip(new_df[comb[0]], new_df[comb[1]])).map(_map)
            # set the unknown value to a new number
            new_df[new_col].fillna(max(_map.values()) + 1, inplace=True)
            new_df[new_col] = new_df[new_col].astype(int)
        return new_df


@register_tool(tags=TAGS)
class GroupStat(MLProcess):
    """
    Aggregate specified column in a DataFrame grouped by another column, adding new features named '<agg_col>_<agg_func>_by_<group_col>'.
    """

    def __init__(self, group_col: str, agg_col: str, agg_funcs: list):
        """
        Initialize self.

        Args:
            group_col (str): Column used for grouping.
            agg_col (str): Column on which aggregation is performed.
            agg_funcs (list): List of aggregation functions to apply, such as ['mean', 'std']. Each function must be supported by pandas.
        """
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
        new_df = df.merge(self.group_df, on=self.group_col, how="left")
        return new_df


@register_tool(tags=TAGS)
class SplitBins(MLProcess):
    """
    Inplace binning of continuous data into intervals, returning integer-encoded bin identifiers directly.
    """

    def __init__(self, cols: list, strategy: str = "quantile"):
        """
        Initialize self.

        Args:
            cols (list): Columns to be binned inplace.
            strategy (str, optional): Strategy used to define the widths of the bins. Enum: ['quantile', 'uniform', 'kmeans']. Defaults to 'quantile'.
        """
        self.cols = cols
        self.strategy = strategy
        self.encoder = None

    def fit(self, df: pd.DataFrame):
        self.encoder = KBinsDiscretizer(strategy=self.strategy, encode="ordinal")
        self.encoder.fit(df[self.cols].fillna(0))

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()
        new_df[self.cols] = self.encoder.transform(new_df[self.cols].fillna(0))
        return new_df


# @register_tool(tags=TAGS)
class ExtractTimeComps(MLProcess):
    """
    Extract time components from a datetime column and add them as new features.
    """

    def __init__(self, time_col: str, time_comps: list):
        """
        Initialize self.

        Args:
            time_col (str): The name of the column containing time data.
            time_comps (list): List of time components to extract. Each component must be in ['year', 'month', 'day', 'hour', 'dayofweek', 'is_weekend'].
        """
        self.time_col = time_col
        self.time_comps = time_comps

    def fit(self, df: pd.DataFrame):
        pass

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        time_s = pd.to_datetime(df[self.time_col], errors="coerce")
        time_comps_df = pd.DataFrame()

        if "year" in self.time_comps:
            time_comps_df["year"] = time_s.dt.year
        if "month" in self.time_comps:
            time_comps_df["month"] = time_s.dt.month
        if "day" in self.time_comps:
            time_comps_df["day"] = time_s.dt.day
        if "hour" in self.time_comps:
            time_comps_df["hour"] = time_s.dt.hour
        if "dayofweek" in self.time_comps:
            time_comps_df["dayofweek"] = time_s.dt.dayofweek + 1
        if "is_weekend" in self.time_comps:
            time_comps_df["is_weekend"] = time_s.dt.dayofweek.isin([5, 6]).astype(int)
        new_df = pd.concat([df, time_comps_df], axis=1)
        return new_df


@register_tool(tags=TAGS)
class GeneralSelection(MLProcess):
    """
    Drop all nan feats and feats with only one unique value.
    """

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

            if df.loc[df[col] == np.inf].shape[0] != 0 or df.loc[df[col] == np.inf].shape[0] != 0:
                feats.remove(col)

            if is_object_dtype(df[col]) and df[col].nunique() == df.shape[0]:
                feats.remove(col)

        self.feats = feats

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df[self.feats + [self.label_col]]
        return new_df


# skip for now because lgb is needed
# @register_tool(tags=TAGS)
class TreeBasedSelection(MLProcess):
    """
    Select features based on tree-based model and remove features with low importance.
    """

    def __init__(self, label_col: str, task_type: str):
        """
        Initialize self.

        Args:
            label_col (str): Label column name.
            task_type (str): Task type, 'cls' for classification, 'mcls' for multi-class classification, 'reg' for regression.
        """
        self.label_col = label_col
        self.task_type = task_type
        self.feats = None

    def fit(self, df: pd.DataFrame):
        params = {
            "boosting_type": "gbdt",
            "objective": "binary",
            "learning_rate": 0.1,
            "num_leaves": 31,
        }

        if self.task_type == "cls":
            params["objective"] = "binary"
            params["metric"] = "auc"
        elif self.task_type == "mcls":
            params["objective"] = "multiclass"
            params["num_class"] = df[self.label_col].nunique()
            params["metric"] = "auc_mu"
        elif self.task_type == "reg":
            params["objective"] = "regression"
            params["metric"] = "rmse"

        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cols = [f for f in num_cols if f not in [self.label_col]]

        dtrain = lgb.Dataset(df[cols], df[self.label_col])
        model = lgb.train(params, dtrain, num_boost_round=100)
        df_imp = pd.DataFrame({"feature_name": dtrain.feature_name, "importance": model.feature_importance("gain")})

        df_imp.sort_values("importance", ascending=False, inplace=True)
        df_imp = df_imp[df_imp["importance"] > 0]
        self.feats = df_imp["feature_name"].tolist()
        self.feats.append(self.label_col)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df[self.feats]
        return new_df


@register_tool(tags=TAGS)
class VarianceBasedSelection(MLProcess):
    """
    Select features based on variance and remove features with low variance.
    """

    def __init__(self, label_col: str, threshold: float = 0):
        """
        Initialize self.

        Args:
            label_col (str): Label column name.
            threshold (float, optional): Threshold for variance. Defaults to 0.
        """
        self.label_col = label_col
        self.threshold = threshold
        self.feats = None
        self.selector = VarianceThreshold(threshold=self.threshold)

    def fit(self, df: pd.DataFrame):
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cols = [f for f in num_cols if f not in [self.label_col]]

        self.selector.fit(df[cols])
        self.feats = df[cols].columns[self.selector.get_support(indices=True)].tolist()
        self.feats.append(self.label_col)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df[self.feats]
        return new_df

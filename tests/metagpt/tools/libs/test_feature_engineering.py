import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import fetch_california_housing, load_breast_cancer, load_iris

from metagpt.tools.libs.feature_engineering import (
    CatCount,
    CatCross,
    ExtractTimeComps,
    GeneralSelection,
    GroupStat,
    KFoldTargetMeanEncoder,
    PolynomialExpansion,
    SplitBins,
    TargetMeanEncoder,
    TreeBasedSelection,
    VarianceBasedSelection,
)


@pytest.fixture
def mock_dataset():
    return pd.DataFrame(
        {
            "num1": [1, 2, np.nan, 4, 5, 6, 7, 3],
            "num2": [1, 3, 2, 1, np.nan, 5, 6, 4],
            "num3": [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "cat1": ["A", "B", np.nan, "D", "E", "C", "B", "A"],
            "cat2": ["A", "A", "A", "A", "A", "A", "A", "A"],
            "date1": [
                "2020-01-01",
                "2020-01-02",
                "2020-01-03",
                "2020-01-04",
                "2020-01-05",
                "2020-01-06",
                "2020-01-07",
                "2020-01-08",
            ],
            "label": [0, 1, 0, 1, 0, 1, 0, 1],
        }
    )


def load_sklearn_data(data_name):
    if data_name == "iris":
        data = load_iris()
    elif data_name == "breast_cancer":
        data = load_breast_cancer()
    elif data_name == "housing":
        data = fetch_california_housing()
    else:
        raise ValueError("data_name not supported")

    X, y, feature_names = data.data, data.target, data.feature_names
    data = pd.DataFrame(X, columns=feature_names)
    data["label"] = y
    return data


def test_polynomial_expansion(mock_dataset):
    pe = PolynomialExpansion(cols=["num1", "num2", "label"], degree=2, label_col="label")
    transformed = pe.fit_transform(mock_dataset)

    assert len(transformed.columns) == len(mock_dataset.columns) + 3

    # when too many columns
    data = load_sklearn_data("breast_cancer")
    cols = [c for c in data.columns if c != "label"]
    pe = PolynomialExpansion(cols=cols, degree=2, label_col="label")
    transformed = pe.fit_transform(data)

    assert len(transformed.columns) == len(data.columns) + 55


def test_cat_count(mock_dataset):
    cc = CatCount(col="cat1")
    transformed = cc.fit_transform(mock_dataset)

    assert "cat1_cnt" in transformed.columns
    assert transformed["cat1_cnt"][0] == 2


def test_target_mean_encoder(mock_dataset):
    tme = TargetMeanEncoder(col="cat1", label="label")
    transformed = tme.fit_transform(mock_dataset)

    assert "cat1_target_mean" in transformed.columns
    assert transformed["cat1_target_mean"][0] == 0.5


def test_kfold_target_mean_encoder(mock_dataset):
    kfme = KFoldTargetMeanEncoder(col="cat1", label="label")
    transformed = kfme.fit_transform(mock_dataset)

    assert "cat1_kf_target_mean" in transformed.columns


def test_cat_cross(mock_dataset):
    cc = CatCross(cols=["cat1", "cat2"])
    transformed = cc.fit_transform(mock_dataset)

    assert "cat1_cat2" in transformed.columns

    cc = CatCross(cols=["cat1", "cat2"], max_cat_num=3)
    transformed = cc.fit_transform(mock_dataset)

    assert "cat1_cat2" not in transformed.columns


def test_group_stat(mock_dataset):
    gs = GroupStat(group_col="cat1", agg_col="num1", agg_funcs=["mean", "sum"])
    transformed = gs.fit_transform(mock_dataset)

    assert "num1_mean_by_cat1" in transformed.columns
    assert "num1_sum_by_cat1" in transformed.columns


def test_split_bins(mock_dataset):
    sb = SplitBins(cols=["num1"])
    transformed = sb.fit_transform(mock_dataset)

    assert transformed["num1"].nunique() <= 5
    assert all(0 <= x < 5 for x in transformed["num1"])


def test_extract_time_comps(mock_dataset):
    time_comps = ["year", "month", "day", "hour", "dayofweek", "is_weekend"]
    etc = ExtractTimeComps(time_col="date1", time_comps=time_comps)
    transformed = etc.fit_transform(mock_dataset.copy())

    for comp in time_comps:
        assert comp in transformed.columns
    assert transformed["year"][0] == 2020
    assert transformed["month"][0] == 1
    assert transformed["day"][0] == 1
    assert transformed["hour"][0] == 0
    assert transformed["dayofweek"][0] == 3
    assert transformed["is_weekend"][0] == 0


def test_general_selection(mock_dataset):
    gs = GeneralSelection(label_col="label")
    transformed = gs.fit_transform(mock_dataset.copy())

    assert "num3" not in transformed.columns
    assert "cat2" not in transformed.columns


@pytest.mark.skip  # skip because TreeBasedSelection needs lgb as dependency
def test_tree_based_selection(mock_dataset):
    # regression
    data = load_sklearn_data("housing")
    tbs = TreeBasedSelection(label_col="label", task_type="reg")
    transformed = tbs.fit_transform(data)
    assert len(transformed.columns) > 1

    # classification
    data = load_sklearn_data("breast_cancer")
    tbs = TreeBasedSelection(label_col="label", task_type="cls")
    transformed = tbs.fit_transform(data)
    assert len(transformed.columns) > 1

    # multi-classification
    data = load_sklearn_data("iris")
    tbs = TreeBasedSelection(label_col="label", task_type="mcls")
    transformed = tbs.fit_transform(data)
    assert len(transformed.columns) > 1


def test_variance_based_selection(mock_dataset):
    vbs = VarianceBasedSelection(label_col="label")
    transformed = vbs.fit_transform(mock_dataset.copy())

    assert "num3" not in transformed.columns

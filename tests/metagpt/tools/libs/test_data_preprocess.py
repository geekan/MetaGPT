from datetime import datetime

import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest

from metagpt.tools.libs.data_preprocess import (
    FillMissingValue,
    LabelEncode,
    MaxAbsScale,
    MinMaxScale,
    OneHotEncode,
    OrdinalEncode,
    RobustScale,
    StandardScale,
    get_column_info,
)


@pytest.fixture
def mock_datasets():
    return pd.DataFrame(
        {
            "num1": [1, 2, np.nan, 4, 5],
            "cat1": ["A", "B", np.nan, "D", "A"],
            "date1": [
                datetime(2020, 1, 1),
                datetime(2020, 1, 2),
                datetime(2020, 1, 3),
                datetime(2020, 1, 4),
                datetime(2020, 1, 5),
            ],
        }
    )


def test_fill_missing_value(mock_datasets):
    fm = FillMissingValue(features=["num1"], strategy="mean")
    transformed = fm.fit_transform(mock_datasets.copy())

    assert transformed["num1"].isnull().sum() == 0


def test_min_max_scale(mock_datasets):
    mms = MinMaxScale(features=["num1"])
    transformed = mms.fit_transform(mock_datasets.copy())

    npt.assert_allclose(transformed["num1"].min(), 0)
    npt.assert_allclose(transformed["num1"].max(), 1)


def test_standard_scale(mock_datasets):
    ss = StandardScale(features=["num1"])
    transformed = ss.fit_transform(mock_datasets.copy())

    assert int(transformed["num1"].mean()) == 0
    assert int(transformed["num1"].std()) == 1


def test_max_abs_scale(mock_datasets):
    mas = MaxAbsScale(features=["num1"])
    transformed = mas.fit_transform(mock_datasets.copy())

    npt.assert_allclose(transformed["num1"].abs().max(), 1)


def test_robust_scale(mock_datasets):
    rs = RobustScale(features=["num1"])
    transformed = rs.fit_transform(mock_datasets.copy())

    assert int(transformed["num1"].median()) == 0


def test_ordinal_encode(mock_datasets):
    oe = OrdinalEncode(features=["cat1"])
    transformed = oe.fit_transform(mock_datasets.copy())

    assert transformed["cat1"].max() == 2


def test_one_hot_encode(mock_datasets):
    ohe = OneHotEncode(features=["cat1"])
    transformed = ohe.fit_transform(mock_datasets.copy())

    assert transformed["cat1_A"].max() == 1


def test_label_encode(mock_datasets):
    le = LabelEncode(features=["cat1"])
    transformed = le.fit_transform(mock_datasets.copy())

    assert transformed["cat1"].max() == 3

    # test transform with unseen data
    test = mock_datasets.copy()
    test["cat1"] = ["A", "B", "C", "D", "E"]
    transformed = le.transform(test)
    assert transformed["cat1"].max() == 4


def test_get_column_info(mock_datasets):
    df = mock_datasets
    column_info = get_column_info(df)

    assert column_info == {
        "Category": ["cat1"],
        "Numeric": ["num1"],
        "Datetime": ["date1"],
        "Others": [],
    }

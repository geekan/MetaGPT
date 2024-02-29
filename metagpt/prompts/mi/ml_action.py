#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 15:43
# @Author  : lidanyang
# @File    : ml_action
# @Desc    :
MODEL_TRAIN_EXAMPLE = """
when current task is "train a lightgbm model on training data", the code can be like:
```python
# Step 1: check data type and convert to numeric
obj_cols = train.select_dtypes(include='object').columns.tolist()

for col in obj_cols:
    encoder = LabelEncoder()
    train[col] = encoder.fit_transform(train[col].unique().tolist() + ['unknown'])
    test[col] = test[col].apply(lambda x: x if x in encoder.classes_ else 'unknown')
    test[col] = encoder.transform(test[col])

# Step 2: train lightgbm model
model = LGBMClassifier()
model.fit(train, y_train)
```end

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
"""

USE_ML_TOOLS_EXAMPLE = """
when current task is "do data preprocess, like fill missing value, handle outliers, etc.", the code can be like:
```python
# Step 1: fill missing value
# Tools used: ['FillMissingValue']
from metagpt.tools.libs.data_preprocess import FillMissingValue

train_processed = train.copy()
test_processed = test.copy()
num_cols = train_processed.select_dtypes(include='number').columns.tolist()
if 'label' in num_cols:
    num_cols.remove('label')
fill_missing_value = FillMissingValue(features=num_cols, strategy='mean')
fill_missing_value.fit(train_processed)
train_processed = fill_missing_value.transform(train_processed)
test_processed = fill_missing_value.transform(test_processed)

# Step 2: handle outliers
for col in num_cols:
    low, high = train_processed[col].quantile([0.01, 0.99])
    train_processed[col] = train_processed[col].clip(low, high)
    test_processed[col] = test_processed[col].clip(low, high)
```end

# Constraints:
- Ensure the output new code is executable in the same Jupyter notebook with previous tasks code have been executed.
- Always prioritize using pre-defined tools for the same functionality.
- Always copy the DataFrame before processing it and use the copy to process.
"""

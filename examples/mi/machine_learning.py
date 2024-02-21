import fire

from metagpt.roles.mi.interpreter import Interpreter

DATA_DIR = "examples/mi/data"
WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."

# sales_forecast data from https://www.kaggle.com/datasets/aslanahmedov/walmart-sales-forecast/data,
# new_train, new_test from train.csv.
SALES_FORECAST_REQ = f"""
# Goal
Use time series regression machine learning to make predictions for Dept sales of the stores as accurate as possible.

# Datasets Available
- train_data: {DATA_DIR}/WalmartSalesForecast/new_train.csv
- test_data: {DATA_DIR}/WalmartSalesForecast/new_test.csv
- additional data: {DATA_DIR}/WalmartSalesForecast/features.csv; To merge on train, test data.
- stores data: {DATA_DIR}/WalmartSalesForecast/stores.csv; To merge on train, test data.

# Metric
The metric of the competition is weighted mean absolute error (WMAE) for test data.

# Notice
- *print* key variables to get more information for next task step.
- Perform data analysis by plotting sales trends, holiday effects, distribution of sales across stores/departments using box/violin on the train data.
- Make sure the DataFrame.dtypes must be int, float or bool, and drop date column.
- Plot scatter plots of  groud truth and predictions on test data.
"""

requirements = {"wine": WINE_REQ, "sales_forecast": SALES_FORECAST_REQ}


async def main(auto_run: bool = True, use_case: str = "wine"):
    mi = Interpreter(auto_run=auto_run)
    await mi.run(requirements[use_case])


if __name__ == "__main__":
    fire.Fire(main)

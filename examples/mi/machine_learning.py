import fire

from metagpt.roles.mi.interpreter import Interpreter

WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."

# DATA_DIR = "your/path/to/data"
DATA_DIR = "examples/mi/data/WalmartSalesForecast2"
# sales_forecast data from https://www.kaggle.com/datasets/aslanahmedov/walmart-sales-forecast/data
SALES_FORECAST_REQ = f"""
# Goal
Train a model to predict sales for each department in every store (split the last 40 weeks records as validation dataset,
the others is train dataset), include plot sales trends, print metric and plot scatter plots of
groud truth and predictions on validation data.

# Datasets Available
- train_data: {DATA_DIR}/train.csv

# Metric
The metric of the competition is weighted mean absolute error (WMAE) for test data.

# Notice
- *print* key variables to get more information for next task step.
"""

REQUIREMENTS = {"wine": WINE_REQ, "sales_forecast": SALES_FORECAST_REQ}


async def main(auto_run: bool = True, use_case: str = "wine"):
    mi = Interpreter(auto_run=auto_run)
    if use_case == "wine":
        requirement = REQUIREMENTS[use_case]
    else:
        mi.use_tools = True
        assert DATA_DIR != "your/path/to/data", f"Please set DATA_DIR for the use_case: {use_case}!"
        requirement = REQUIREMENTS[use_case]
    await mi.run(requirement)


if __name__ == "__main__":
    fire.Fire(main)

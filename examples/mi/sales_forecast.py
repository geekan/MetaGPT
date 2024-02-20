from metagpt.roles.mi.interpreter import Interpreter


async def main():
    # data from https://www.kaggle.com/datasets/aslanahmedov/walmart-sales-forecast/data
    train_data = "examples/mi/data/WalmartSalesForecast/new_train.csv"
    test_data = "examples/mi/data/WalmartSalesForecast/new_test.csv"
    features = "examples/mi/data/WalmartSalesForecast/features.csv"
    stores = "examples/mi/data/WalmartSalesForecast/stores.csv"

    prompt = f"""
    # Goal
    Use time series regression machine learning to make predictions for Dept sales of the stores as accurate as possible.

    # Datasets Available
    - train_data: {train_data}
    - test_data: {test_data}
    - additional data: {features}, merge on train, test data.
    - stores data: {stores}, merge on train, test data.

    # Metric
    The metric of the competition is weighted mean absolute error (WMAE) for test data.

    # Notice
    - *print* key variables to get more information for next task step.
    - Make sure the DataFrame.dtypes must be int, float or bool, and drop date column.
    """
    # it will be better if autogloun had been installed. https://auto.gluon.ai/stable/install.html
    mi = Interpreter(use_tools=True)

    await mi.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

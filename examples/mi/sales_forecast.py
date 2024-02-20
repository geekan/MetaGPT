from metagpt.roles.mi.interpreter import Interpreter


async def main():
    # data from https://www.kaggle.com/datasets/aslanahmedov/walmart-sales-forecast/data
    data_dir = "examples/mi/data/WalmartSalesForecast"
    train_data = f"{data_dir}/new_train.csv"
    test_data = f"{data_dir}/new_test.csv"
    features = f"{data_dir}/features.csv"
    stores = f"{data_dir}/stores.csv"

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
    - Perform data analysis by plotting sales trends, holiday effects, distribution of sales across stores/departments using box/violin on the train data.
    - Make sure the DataFrame.dtypes must be int, float or bool, and drop date column.
    - Plot scatter plots of  groud truth and predictions on test data.
    """
    # it will be better if autogloun had been installed. https://auto.gluon.ai/stable/install.html
    mi = Interpreter(use_tools=True)

    await mi.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

from metagpt.roles.di.data_analyst import DataAnalyst

HOUSE_PRICE_TRAIN_PATH = "/data/house-prices-advanced-regression-techniques/split_train.csv"
HOUSE_PRICE_EVAL_PATH = "/data/house-prices-advanced-regression-techniques/split_eval.csv"
HOUSE_PRICE_REQ = f"""
This is a house price dataset, your goal is to predict the sale price of a property based on its features. The target column is SalePrice. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report RMSE between the logarithm of the predicted value and the logarithm of the observed sales price on the eval data. Train data path: '{HOUSE_PRICE_TRAIN_PATH}', eval data path: '{HOUSE_PRICE_EVAL_PATH}'.
"""

CALIFORNIA_HOUSING_REQ = """
Analyze the 'Canifornia-housing-dataset' using https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html#sklearn.datasets.fetch_california_housing to predict the median house value. you need to perfrom data preprocessing, feature engineering and finally modeling to predict the target. Use machine learning techniques such as linear regression (including ridge regression and lasso regression), random forest, CatBoost, LightGBM, XGBoost or other appropriate method. You also need to report the MSE on the test dataset
"""

# For web scraping task, please provide url begin with `https://` or `http://`
PAPER_LIST_REQ = """"
Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
and save it to a csv file. paper title must include `multiagent` or `large language model`.
**Notice: view the page element before writing scraping code**
"""

ECOMMERCE_REQ = """
Get products data from website https://scrapeme.live/shop/ and save it as a csv file.
The first page product name, price, product URL, and image URL must be saved in the csv.
**Notice: view the page element before writing scraping code**
"""

NEWS_36KR_REQ = """从36kr创投平台https://pitchhub.36kr.com/financing-flash 所有初创企业融资的信息, **注意: 这是一个中文网站**;
下面是一个大致流程, 你会根据每一步的运行结果对当前计划中的任务做出适当调整:
1. 爬取并本地保存html结构;
2. 直接打印第7个*`快讯`*关键词后2000个字符的html内容, 作为*快讯的html内容示例*;
3. 反思*快讯的html内容示例*中的规律, 设计正则匹配表达式来获取*`快讯`*的标题、链接、时间;
4. 筛选最近3天的初创企业融资*`快讯`*, 以list[dict]形式打印前5个。
5. 将全部结果存在本地csv中
**Notice: view the page element before writing scraping code**
"""

WIKIPEDIA_SEARCH_REQ = """
Search for `LLM` on https://www.wikipedia.org/ and print all the meaningful significances of the entry.
"""

STACKOVERFLOW_CLICK_REQ = """
Click the Questions tag in https://stackoverflow.com/ and scrap question name, votes, answers and views num to csv in the first result page.
"""


async def main():
    di = DataAnalyst()
    await di.browser.start()
    await di.run(STACKOVERFLOW_CLICK_REQ)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

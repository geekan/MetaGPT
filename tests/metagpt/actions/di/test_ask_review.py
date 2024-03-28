import pytest

from metagpt.actions.di.ask_review import AskReview, ReviewConst
from metagpt.schema import AIMessage, Message, Plan, Task


@pytest.mark.asyncio
async def test_ask_review(mocker):
    mock_review_input = "confirm"
    mocker.patch("builtins.input", return_value=mock_review_input)
    rsp, confirmed = await AskReview().run(review_type="human")
    assert rsp == mock_review_input
    assert confirmed


@pytest.mark.asyncio
async def test_ask_review_llm():
    context = [
        Message("task instruction: Train a model to predict wine class using the training set."),
        AIMessage(
            """
            from sklearn.datasets import load_wine
            wine_data = load_wine()
            plt.hist(wine_data.target, bins=len(wine_data.target_names))
            plt.xlabel('Class')
            plt.ylabel('Number of Samples')
            plt.title('Distribution of Wine Classes')
            plt.xticks(range(len(wine_data.target_names)), wine_data.target_names)
            plt.show()
            """.strip()
        ),
    ]
    rsp, confirmed = await AskReview().run(context, review_type="llm")
    assert rsp.startswith(("redo", "change"))
    assert not confirmed


@pytest.fixture()
def unreasonable_plan():
    CONTEXT = """
    ## User Requirement
    "Get paper list that title must include `multiagent` or `large language model` from table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,and save it to a csv file.[I have confirmed the robot protocol, and it is permissible to crawl the website.]"
    ## Context

    ## Current Plan

    ## Current Task

    """
    # 不合理的地方是有很多未知信息需要先探索：1）网页中的哪张表格是论文表；2）论文表的哪个字段是标题；
    unreasonable_plan = """
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Scrape the list of paper titles from the ICLR 2024 statistics page that include 'multiagent' or 'large language model'.",
            "task_type": "web scraping"
        },
        {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Save the scraped list of paper titles to a CSV file.",
            "task_type": "data preprocessing"
        }
    ]
    """
    return [Message(CONTEXT), AIMessage(unreasonable_plan)]


@pytest.fixture()
def reasonable_plan():
    CONTEXT = """
    ## User Requirement
    "Get paper list that title must include `multiagent` or `large language model` from table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,and save it to a csv file.[I have confirmed the robot protocol, and it is permissible to crawl the website.]"
    ## Context

    ## Current Plan

    ## Current Task

    """
    reasonable_plan = """
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Programmatically confirm the robot protocol at https://papercopilot.com/robots.txt, and ensure that scraping the ICLR 2024 statistics page is allowed."
        },
        {
            "task_id": "2",
            "dependent_task_ids": ["1"],
            "instruction": "Access the website https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/, parse the web structure using an HTML parser, and locate the specific table with ICLR 2024 paper information."
        },
        {
            "task_id": "3",
            "dependent_task_ids": ["2"],
            "instruction": "Confirm the accessibility and structure of the website to ensure proper scraping. Verify that the identified table contains the necessary paper information."
        },
        {
            "task_id": "4",
            "dependent_task_ids": ["3"],
            "instruction": "Extract the data from the identified table, ensuring to capture all relevant columns."
        },
        {
            "task_id": "5",
            "dependent_task_ids": ["4"],
            "instruction": "Filter the extracted data to include only papers with titles containing `multiagent` or `large language model`, performing a case-insensitive search."
        },
        {
            "task_id": "6",
            "dependent_task_ids": ["5"],
            "instruction": "Define the CSV file structure, including headers for the relevant columns such as title, authors, abstract, and publication date. Specify the format for saving the paper titles."
        },
        {
            "task_id": "7",
            "dependent_task_ids": ["6"],
            "instruction": "Save the filtered data to a CSV file named 'filtered_papers.csv' in a specified directory, and handle any exceptions or errors during the saving process."
        },
        {
            "task_id": "8",
            "dependent_task_ids": ["7"],
            "instruction": "Validate the CSV file to ensure the data is correctly formatted and complete."
        },
        {
            "task_id": "9",
            "dependent_task_ids": ["8"],
            "instruction": "Test the robustness of the scraping script against potential future changes in the website structure."
        }
    ]
    """
    return [Message(CONTEXT), AIMessage(reasonable_plan)]


@pytest.fixture
def early_stop_context_plan():
    CONTEXT = """
    ## User Requirement
    "Run data analysis on sklearn Iris dataset, include a plot"
    ## Context

    ## Current Plan
    [
        {
            "task_id": "1",
            "dependent_task_ids": [],
            "instruction": "Load the sklearn Iris dataset and perform exploratory data analysis",
            "task_type": "eda",
            "code": "",
            "result": "",
            "is_success": false,
            "is_finished": false
        },
        {
            "task_id": "2",
            "dependent_task_ids": [
                "1"
            ],
            "instruction": "Create a plot visualizing the distribution of the different features in the Iris dataset",
            "task_type": "other",
            "code": "",
            "result": "",
            "is_success": false,
            "is_finished": false
        }
    ]
    ## Current Task
    {"task_id":"1","dependent_task_ids":[],"instruction":"Load the sklearn Iris dataset and perform exploratory data analysis","task_type":"eda","code":"","result":"","is_success":false,"is_finished":false}
    """
    task1 = Task(task_id="1", instruction="Load the sklearn Iris dataset and perform exploratory data analysis")
    task2 = Task(
        task_id="2",
        instruction="Create a plot visualizing the distribution of the different features in the Iris dataset",
    )
    plan = Plan(goal="Run data analysis on sklearn Iris dataset, include a plot", tasks=[task1, task2])
    working_memory = [
        AIMessage(
            """current task generated code is:
                import numpy as np
                from sklearn import datasets
                import pandas as pd
                import seaborn as sns
                import matplotlib.pyplot as plt

                # Load the Iris dataset
                iris = datasets.load_iris()
                iris_df = pd.DataFrame(data= np.c_[iris['data'], iris['target']],
                                    columns= iris['feature_names'] + ['target'])

                # Convert the target to a categorical variable
                iris_df['species'] = pd.Categorical.from_codes(iris.target, iris.target_names)

                # Perform exploratory data analysis
                # Distinguish column types
                numerical_cols = iris_df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = iris_df.select_dtypes(include=[object]).columns.tolist()

                # Summary statistics for numerical columns
                print(iris_df[numerical_cols].describe())

                # Pairplot to visualize the relationships between numerical variables
                sns.pairplot(iris_df, hue='species')
                plt.show()

                # Correlation matrix for numerical variables
                corr_matrix = iris_df[numerical_cols].corr()
                print(corr_matrix)

                # Heatmap of the correlation matrix
                sns.heatmap(corr_matrix, annot=True)
                plt.show()"""
        ),
        Message(
            """current task code execution result:
                sepal length (cm)  sepal width (cm)  petal length (cm)  \
                count         150.000000        150.000000         150.000000   
                mean            5.843333          3.057333           3.758000   
                std             0.828066          0.435866           1.765298   
                min             4.300000          2.000000           1.000000   
                25%             5.100000          2.800000           1.600000   
                50%             5.800000          3.000000           4.350000   
                75%             6.400000          3.300000           5.100000   
                max             7.900000          4.400000           6.900000   

                    petal width (cm)      target  
                count        150.000000  150.000000  
                mean           1.199333    1.000000  
                std            0.762238    0.819232  
                min            0.100000    0.000000  
                25%            0.300000    0.000000  
                50%            1.300000    1.000000  
                75%            1.800000    2.000000  
                max            2.500000    2.000000  
                ,/Users/vicis/opt/anaconda3/envs/metagpt/lib/python3.9/site-packages/seaborn/axisgrid.py:123: UserWarning: The figure layout has changed to tight
                self._figure.tight_layout(*args, **kwargs)
                ,,                   sepal length (cm)  sepal width (cm)  petal length (cm)  \
                sepal length (cm)           1.000000         -0.117570           0.871754   
                sepal width (cm)           -0.117570          1.000000          -0.428440   
                petal length (cm)           0.871754         -0.428440           1.000000   
                petal width (cm)            0.817941         -0.366126           0.962865   
                target                      0.782561         -0.426658           0.949035   

                                petal width (cm)    target  
                sepal length (cm)          0.817941  0.782561  
                sepal width (cm)          -0.366126 -0.426658  
                petal length (cm)          0.962865  0.949035  
                petal width (cm)           1.000000  0.956547  
                target                     0.956547  1.000000 
                """
        ),
    ]
    return [Message(CONTEXT)] + working_memory, plan


@pytest.mark.asyncio
async def test_llm_review_unreasonable_plan(unreasonable_plan):
    rsp, confirmed = await AskReview().run(
        unreasonable_plan, trigger=ReviewConst.PLAN_REVIEW_TRIGGER, review_type="llm"
    )
    print(rsp)
    assert not confirmed
    assert rsp.startswith("change")


@pytest.mark.asyncio
async def test_llm_review_reasonable_plan(reasonable_plan):
    # test reasonable plan
    rsp, confirmed = await AskReview().run(reasonable_plan, trigger=ReviewConst.PLAN_REVIEW_TRIGGER, review_type="llm")
    print(rsp)
    assert confirmed
    assert rsp.startswith("confirm")


@pytest.mark.asyncio
async def test_finished_review(early_stop_context_plan):
    context, plan = early_stop_context_plan
    rsp, confirmed = await AskReview().run(context, plan, trigger=ReviewConst.TASK_REVIEW_TRIGGER, review_type="llm")
    print(rsp)
    assert confirmed
    assert rsp.startswith("finished")
    assert len(plan.get_finished_tasks()) == 2

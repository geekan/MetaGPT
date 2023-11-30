import pytest

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_code_running():
    pi = ExecutePyCode()
    output = await pi.run("print('hello world!')")
    assert output[1] is True
    output = await pi.run({"code": "print('hello world!')", "language": "python"})
    assert output[1] is True
    code_msg = Message("print('hello world!')")
    output = await pi.run(code_msg)
    assert output[1] is True


@pytest.mark.asyncio
async def test_split_code_running():
    pi = ExecutePyCode()
    output = await pi.run("x=1\ny=2")
    output = await pi.run("z=x+y")
    output = await pi.run("assert z==3")
    assert output[1] is True


@pytest.mark.asyncio
async def test_execute_error():
    pi = ExecutePyCode()
    output = await pi.run("z=1/0")
    assert output[1] is False


@pytest.mark.asyncio
async def test_plotting_code():
    pi = ExecutePyCode()
    code = """
    import numpy as np
    import matplotlib.pyplot as plt

    # 生成随机数据
    random_data = np.random.randn(1000)  # 生成1000个符合标准正态分布的随机数

    # 绘制直方图
    plt.hist(random_data, bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')

    # 添加标题和标签
    plt.title('Histogram of Random Data')
    plt.xlabel('Value')
    plt.ylabel('Frequency')

    # 显示图形
    plt.show()
    """
    output = await pi.run(code)
    assert output[1] is True


@pytest.mark.asyncio
async def test_plotting_bug():
    code = """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from sklearn.datasets import load_iris
    # Load the Iris dataset
    iris_data = load_iris()
    # Convert the loaded Iris dataset into a DataFrame for easier manipulation
    iris_df = pd.DataFrame(iris_data['data'], columns=iris_data['feature_names'])
    # Add a column for the target
    iris_df['species'] = pd.Categorical.from_codes(iris_data['target'], iris_data['target_names'])
    # Set the style of seaborn
    sns.set(style='whitegrid')
    # Create a pairplot of the iris dataset
    plt.figure(figsize=(10, 8))
    pairplot = sns.pairplot(iris_df, hue='species')
    # Show the plot
    plt.show()
    """
    pi = ExecutePyCode()
    output = await pi.run(code)
    assert output[1] is True

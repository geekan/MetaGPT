import pytest

from metagpt.actions import ExecutePyCode
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_code_running():
    pi = ExecutePyCode()
    output = await pi.run("print('hello world!')")
    assert output.state == "done"
    output = await pi.run({"code": "print('hello world!')", "language": "python"})
    assert output.state == "done"
    code_msg = Message("print('hello world!')")
    output = await pi.run(code_msg)
    assert output.state == "done"


@pytest.mark.asyncio
async def test_split_code_running():
    pi = ExecutePyCode()
    output = await pi.run("x=1\ny=2")
    output = await pi.run("z=x+y")
    output = await pi.run("assert z==3")
    assert output.state == "done"


@pytest.mark.asyncio
async def test_execute_error():
    pi = ExecutePyCode()
    output = await pi.run("z=1/0")
    assert output.state == "error"


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
    assert output.state == "done"

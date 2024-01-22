import pytest

from metagpt.actions.execute_code import ExecutePyCode, truncate


@pytest.mark.asyncio
async def test_code_running():
    pi = ExecutePyCode()
    output = await pi.run("print('hello world!')")
    assert output[1] is True
    output = await pi.run({"code": "print('hello world!')", "language": "python"})
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
    plt.close()
    """
    output = await pi.run(code)
    assert output[1] is True


def test_truncate():
    # 代码执行成功
    output, is_success = truncate("hello world", 5, True)
    assert "Truncated to show only first 5 characters\nhello" in output
    assert is_success
    # 代码执行失败
    output, is_success = truncate("hello world", 5, False)
    assert "Truncated to show only last 5 characters\nworld" in output
    assert not is_success
    # 异步
    output, is_success = truncate("<coroutine object", 5, True)
    assert not is_success
    assert "await" in output
    # 重复的desc
    result = "Executed code successfully. Truncated to show only first 5 characters\nhello"
    output, is_success = truncate(result, 5, True)
    assert is_success
    assert output == result


@pytest.mark.asyncio
async def test_run_with_timeout():
    pi = ExecutePyCode(timeout=1)
    code = "import time; time.sleep(2)"
    message, success = await pi.run(code)
    assert not success
    assert message.startswith("Cell execution timed out")


@pytest.mark.asyncio
async def test_run_code_text():
    pi = ExecutePyCode()
    message, success = await pi.run(code='print("This is a code!")', language="python")
    assert success
    assert message == "This is a code!\n"
    message, success = await pi.run(code="# This is a code!", language="markdown")
    assert success
    assert message == "# This is a code!"
    mix_text = "# Title!\n ```python\n print('This is a code!')```"
    message, success = await pi.run(code=mix_text, language="markdown")
    assert success
    assert message == mix_text


@pytest.mark.asyncio
async def test_terminate():
    pi = ExecutePyCode()
    await pi.run(code='print("This is a code!")', language="python")
    is_kernel_alive = await pi.nb_client.km.is_alive()
    assert is_kernel_alive
    await pi.terminate()
    import time

    time.sleep(2)
    assert pi.nb_client.km is None


@pytest.mark.asyncio
async def test_reset():
    pi = ExecutePyCode()
    await pi.run(code='print("This is a code!")', language="python")
    is_kernel_alive = await pi.nb_client.km.is_alive()
    assert is_kernel_alive
    await pi.reset()
    assert pi.nb_client.km is None

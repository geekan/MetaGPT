import pytest

from metagpt.actions.di.execute_nb_code import ExecuteNbCode


@pytest.mark.asyncio
async def test_code_running():
    executor = ExecuteNbCode()
    output, is_success = await executor.run("print('hello world!')")
    assert is_success
    await executor.terminate()


@pytest.mark.asyncio
async def test_split_code_running():
    executor = ExecuteNbCode()
    _ = await executor.run("x=1\ny=2")
    _ = await executor.run("z=x+y")
    output, is_success = await executor.run("assert z==3")
    assert is_success
    await executor.terminate()


@pytest.mark.asyncio
async def test_execute_error():
    executor = ExecuteNbCode()
    output, is_success = await executor.run("z=1/0")
    assert not is_success
    await executor.terminate()


PLOT_CODE = """
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


@pytest.mark.asyncio
async def test_plotting_code():
    executor = ExecuteNbCode()
    output, is_success = await executor.run(PLOT_CODE)
    assert is_success
    await executor.terminate()


@pytest.mark.asyncio
async def test_run_with_timeout():
    executor = ExecuteNbCode(timeout=1)
    code = "import time; time.sleep(2)"
    message, success = await executor.run(code)
    assert not success
    assert message.startswith("Cell execution timed out")
    await executor.terminate()


@pytest.mark.asyncio
async def test_run_code_text():
    executor = ExecuteNbCode()
    message, success = await executor.run(code='print("This is a code!")', language="python")
    assert success
    assert "This is a code!" in message
    message, success = await executor.run(code="# This is a code!", language="markdown")
    assert success
    assert message == "# This is a code!"
    mix_text = "# Title!\n ```python\n print('This is a code!')```"
    message, success = await executor.run(code=mix_text, language="markdown")
    assert success
    assert message == mix_text
    await executor.terminate()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "k", [(1), (5)]
)  # k=1 to test a single regular terminate, k>1 to test terminate under continuous run
async def test_terminate(k):
    for _ in range(k):
        executor = ExecuteNbCode()
        await executor.run(code='print("This is a code!")', language="python")
        is_kernel_alive = await executor.nb_client.km.is_alive()
        assert is_kernel_alive
        await executor.terminate()
        assert executor.nb_client.km is None
        assert executor.nb_client.kc is None


@pytest.mark.asyncio
async def test_reset():
    executor = ExecuteNbCode()
    await executor.run(code='print("This is a code!")', language="python")
    is_kernel_alive = await executor.nb_client.km.is_alive()
    assert is_kernel_alive
    await executor.reset()
    assert executor.nb_client.km is None
    await executor.terminate()


@pytest.mark.asyncio
async def test_parse_outputs():
    executor = ExecuteNbCode()
    code = """
    import pandas as pd
    df = pd.DataFrame({'ID': [1,2,3], 'NAME': ['a', 'b', 'c']})
    print(df.columns)
    print(f"columns num:{len(df.columns)}")
    print(df['DUMMPY_ID'])
    """
    output, is_success = await executor.run(code)
    assert not is_success
    assert "Index(['ID', 'NAME'], dtype='object')" in output
    assert "KeyError: 'DUMMPY_ID'" in output
    assert "columns num:2" in output
    await executor.terminate()

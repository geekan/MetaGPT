import pytest

from metagpt.tools.code_executor.pyexe import AsyncPyExecutor


@pytest.mark.asyncio
async def test_async_save():
    pyer = AsyncPyExecutor("./tests/data/code_executor/pyexe", True)
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(["print('Hello from Python!')"])
    await python_code_gen.asend(["a = 1;b=2;c=3"])
    await python_code_gen.asend(["print(a + b)"])
    await python_code_gen.asend(["print(globals())"])
    pyer.print_cmd_space()
    # 停止python进程
    await pyer.terminate()
    assert len(pyer._cmd_space) == 4


@pytest.mark.asyncio
async def test_async_load():
    work_dir = "./tests/data/code_executor/pyexe"
    pyer = AsyncPyExecutor(work_dir).load()
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(["print(2*a + b + c)"])
    pyer.print_cmd_space()
    # 停止python进程
    await pyer.terminate()
    assert len(pyer._cmd_space) == 5
    assert pyer._cmd_space["4"]["stdout"] == "7"


@pytest.mark.asyncio
async def test_async_script():
    pyer = AsyncPyExecutor("./tests/data/code_executor/pyexe", True)
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(
        "tests/data/code_executor/hi_python.py"
    )  # 注意: 如果没有if __name__ == "__main__" 语句，python脚本无法执行
    pyer.print_cmd_space()
    # 停止python进程
    await pyer.terminate()
    assert len(pyer._cmd_space) == 1
    assert "Hello from Python!" in pyer._cmd_space["0"]["stdout"]
    assert "3" in pyer._cmd_space["0"]["stdout"]
    assert "6" in pyer._cmd_space["0"]["stdout"]

import os
import tempfile

import pytest

from metagpt.actions.clone_function import (
    CloneFunction,
    run_function_code,
    run_function_script,
)

source_code = """
import pandas as pd
import ta

def user_indicator():
    # 读取股票数据
    stock_data = pd.read_csv('./tests/data/baba_stock.csv')
    stock_data.head()
    # 计算简单移动平均线
    stock_data['SMA'] = ta.trend.sma_indicator(stock_data['Close'], window=6)
    stock_data[['Date', 'Close', 'SMA']].head()
    # 计算布林带
    stock_data['bb_upper'], stock_data['bb_middle'], stock_data['bb_lower'] = ta.volatility.bollinger_hband_indicator(stock_data['Close'], window=20), ta.volatility.bollinger_mavg(stock_data['Close'], window=20), ta.volatility.bollinger_lband_indicator(stock_data['Close'], window=20)
    stock_data[['Date', 'Close', 'bb_upper', 'bb_middle', 'bb_lower']].head()
"""

template_code = """
def stock_indicator(stock_path: str, indicators=['Simple Moving Average', 'BollingerBands', 'MACD]) -> pd.DataFrame:
    import pandas as pd
    # here is your code.
"""


def get_expected_res():
    import pandas as pd
    import ta

    # 读取股票数据
    stock_data = pd.read_csv("./tests/data/baba_stock.csv")
    stock_data.head()
    # 计算简单移动平均线
    stock_data["SMA"] = ta.trend.sma_indicator(stock_data["Close"], window=6)
    stock_data[["Date", "Close", "SMA"]].head()
    # 计算布林带
    stock_data["bb_upper"], stock_data["bb_middle"], stock_data["bb_lower"] = (
        ta.volatility.bollinger_hband_indicator(stock_data["Close"], window=20),
        ta.volatility.bollinger_mavg(stock_data["Close"], window=20),
        ta.volatility.bollinger_lband_indicator(stock_data["Close"], window=20),
    )
    stock_data[["Date", "Close", "bb_upper", "bb_middle", "bb_lower"]].head()
    return stock_data


@pytest.mark.asyncio
async def test_clone_function():
    clone = CloneFunction()
    code = await clone.run(template_code, source_code)
    assert "def " in code
    stock_path = "./tests/data/baba_stock.csv"
    df, msg = run_function_code(code, "stock_indicator", stock_path)
    assert not msg
    expected_df = get_expected_res()
    assert df.equals(expected_df)


def test_run_function_script():
    # 创建一个临时文件并写入脚本内容
    script_content = """def valid_function(arg1, arg2):\n    return arg1 + arg2\n"""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(script_content)
        temp_file_path = temp_file.name

    invalid_script_content = """def valid_function(arg1, arg2)\n    return arg1 + arg2\n"""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as error_temp_file:
        error_temp_file.write(invalid_script_content)
        error_temp_file_path = error_temp_file.name

    try:
        # 正常情况下运行脚本
        result, _ = run_function_script(temp_file_path, "valid_function", 1, arg2=2)
        assert result == 3

        # 不存在的脚本路径
        with pytest.raises(FileNotFoundError):
            run_function_script("nonexistent/path/script.py", "valid_function", 1, arg2=2)

        # 无效的脚本内容
        result, traceback = run_function_script(error_temp_file_path, "invalid_function", 1, arg2=2)
        assert not result
        assert "SyntaxError" in traceback

        # 函数调用失败的情况
        result, traceback = run_function_script(temp_file_path, "function_that_raises_exception", 1, arg2=2)
        assert not result
        assert "KeyError" in traceback

    finally:
        # 删除临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

import pytest

from metagpt.actions.clone_function import CloneFunction, run_function_code


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
    stock_data = pd.read_csv('./tests/data/baba_stock.csv')
    stock_data.head()
    # 计算简单移动平均线
    stock_data['SMA'] = ta.trend.sma_indicator(stock_data['Close'], window=6)
    stock_data[['Date', 'Close', 'SMA']].head()
    # 计算布林带
    stock_data['bb_upper'], stock_data['bb_middle'], stock_data['bb_lower'] = ta.volatility.bollinger_hband_indicator(stock_data['Close'], window=20), ta.volatility.bollinger_mavg(stock_data['Close'], window=20), ta.volatility.bollinger_lband_indicator(stock_data['Close'], window=20)
    stock_data[['Date', 'Close', 'bb_upper', 'bb_middle', 'bb_lower']].head()
    return stock_data


@pytest.mark.asyncio
async def test_clone_function():
    clone = CloneFunction()
    code = await clone.run(template_code, source_code)
    assert 'def ' in code
    stock_path = './tests/data/baba_stock.csv'
    df, msg = run_function_code(code, 'stock_indicator', stock_path)
    assert not msg
    expected_df = get_expected_res()
    assert df.equals(expected_df)

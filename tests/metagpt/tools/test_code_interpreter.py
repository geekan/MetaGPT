import pytest
import pandas as pd
from pathlib import Path

from tests.data import sales_desc, store_desc
from metagpt.tools.code_interpreter import OpenCodeInterpreter, OpenInterpreterDecorator
from metagpt.actions import Action
from metagpt.logs import logger


logger.add('./tests/data/test_ci.log')
stock = "./tests/data/baba_stock.csv"


# TODO: 需要一种表格数据格式，能够支持schame管理的，标注字段类型和字段含义。
class CreateStockIndicators(Action):
    @OpenInterpreterDecorator(save_code=True, code_file_path="./tests/data/stock_indicators.py")
    async def run(self, stock_path: str, indicators=['Simple Moving Average', 'BollingerBands']) -> pd.DataFrame:
        """对stock_path中的股票数据, 使用pandas和ta计算indicators中的技术指标, 返回带有技术指标的股票数据，不需要去除空值, 不需要安装任何包；
            指标生成对应的三列: SMA, BB_upper, BB_lower
        """
        ...


@pytest.mark.asyncio
async def test_actions():
    # 计算指标
    indicators = ['Simple Moving Average', 'BollingerBands']
    stocker = CreateStockIndicators()
    df, msg = await stocker.run(stock, indicators=indicators)
    assert isinstance(df, pd.DataFrame)
    assert 'Close' in df.columns
    assert 'Date' in df.columns
    # 将df保存为文件，将文件路径传入到下一个action
    df_path = './tests/data/stock_indicators.csv'
    df.to_csv(df_path)
    assert Path(df_path).is_file()
    # 可视化指标结果
    figure_path = './tests/data/figure_ci.png'
    ci_ploter = OpenCodeInterpreter()
    ci_ploter.chat(f"使用seaborn对{df_path}中与股票布林带有关的数据列的Date, Close, SMA, BB_upper（布林带上界）, BB_lower（布林带下界）进行可视化, 可视化图片保存在{figure_path}中。不需要任何指标计算，把Date列转换为日期类型。要求图片优美，BB_upper, BB_lower之间使用合适的颜色填充。")
    assert Path(figure_path).is_file()

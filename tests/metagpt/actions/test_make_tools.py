import pytest

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.make_tools import MakeTools
from metagpt.logs import logger


@pytest.mark.asyncio
async def test_make_tools():
    code = "import yfinance as yf\n\n# Collect Alibaba stock data\nalibaba = yf.Ticker('BABA')\ndata = alibaba.history(period='1d', start='2022-01-01', end='2022-12-31')\nprint(data.head())"
    msgs = [{'role': 'assistant', 'content': code}]
    mt = MakeTools()
    tool_code = await mt.run(msgs)
    logger.debug(tool_code)
    ep = ExecutePyCode()
    tool_code = "!pip install yfinance\n" + tool_code
    result, res_type = await ep.run(tool_code)
    assert res_type is True
    logger.debug(result)


@pytest.mark.asyncio
async def test_make_tools2():
    code = '''import pandas as pd\npath = "./tests/data/test.csv"\ndf = pd.read_csv(path)\ndata = df.copy()\n
    data['started_at'] = data['started_at'].apply(lambda r: pd.to_datetime(r))\n
    data['ended_at'] = data['ended_at'].apply(lambda r: pd.to_datetime(r))\ndata.head()'''
    msgs = [{'role': 'assistant', 'content': code}]
    mt = MakeTools()
    tool_code = await mt.run(msgs)
    logger.debug(tool_code)
    ep = ExecutePyCode()
    tool_code = tool_code
    result, res_type = await ep.run(tool_code)
    assert res_type is True
    logger.debug(result)


@pytest.mark.asyncio
async def test_make_tools3():
    code = '''import pandas as pd\npath = "./tests/data/test.csv"\ndf = pd.read_csv(path)\ndata = df.copy()\n
    data['started_at'] = data['started_at'].apply(lambda r: pd.to_datetime(r))\n
    data['ended_at'] = data['ended_at'].apply(lambda r: pd.to_datetime(r))\n
    data['duration_hour'] = (data['ended_at'] - data['started_at']).dt.seconds/3600\ndata.head()'''
    msgs = [{'role': 'assistant', 'content': code}]
    mt = MakeTools()
    tool_code = await mt.run(msgs)
    logger.debug(tool_code)
    ep = ExecutePyCode()
    tool_code = tool_code
    result, res_type = await ep.run(tool_code)
    assert res_type is True
    logger.debug(result)

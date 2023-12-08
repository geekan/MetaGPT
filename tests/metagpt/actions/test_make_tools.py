import pytest

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.make_tools import MakeTools


@pytest.mark.asyncio
async def test_make_tools():
    code = "import yfinance as yf\n\n# Collect Alibaba stock data\nalibaba = yf.Ticker('BABA')\ndata = alibaba.history(period='1d', start='2022-01-01', end='2022-12-31')\nprint(data.head())"
    msgs = [{'role': 'assistant', 'content': code}]
    mt = MakeTools()
    tool_code = await mt.run(msgs)
    print(tool_code)
    ep = ExecutePyCode()
    tool_code = "!pip install yfinance\n" + tool_code
    result, res_type = await ep.run(tool_code)
    assert res_type is True
    print(result)

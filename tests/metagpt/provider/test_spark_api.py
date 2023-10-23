from metagpt.logs import logger
from metagpt.provider.spark_api import SparkAPI


def test_message():
    llm = SparkAPI()

    logger.info(llm.ask('只回答"收到了"这三个字。'))
    result = llm.ask('写一篇五百字的日记')
    logger.info(result)
    assert len(result) > 100

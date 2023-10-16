from metagpt.provider.spark_api import SparkAPI
def test_message():
    llm=SparkAPI()
    llm.ask('只回答"收到了"这三个字。')
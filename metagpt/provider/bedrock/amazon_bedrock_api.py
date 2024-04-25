
import json
from typing import Coroutine, Literal
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM
from metagpt.logs import log_llm_stream, logger
from botocore.config import Config
import boto3


@register_provider([LLMType.AMAZON_BEDROCK])
class AmazonBedrockLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.__client = self.__init_client("bedrock-runtime")

    def __init_client(self, service_name: Literal["bedrock-runtime", "bedrock"]):
        # access key from https://us-east-1.console.aws.amazon.com/iam
        self.__credentital_kwards = {
            "aws_secret_access_key": self.config.secret_key,
            "aws_access_key_id": self.config.access_key,
            "region_name": self.config.region_name
        }
        session = boto3.Session(**self.__credentital_kwards)
        client = session.client(service_name)
        return client

    def list_models(self):
        """see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock/client/list_foundation_models.html"""
        client = self.__init_client("bedrock")
        # only output text-generation models
        response = client.list_foundation_models(byOutputModality='TEXT')
        summaries = [f'{summary.get("modelId", ""):50} Support Streaming:{summary.get("responseStreamingSupported","")}'
                     for summary in response.get("modelSummaries", {})]
        logger.info("\n"+"\n".join(summaries))

    def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        pass

    def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        pass

    def completion(self, messages):
        pass

    def acompletion(self, messages: list[dict]):
        pass


if __name__ == '__main__':
    from .config import my_config
    prompt = "who are you?"
    messages = [{"role": "user", "content": prompt}]
    llm = AmazonBedrockLLM(my_config)
    llm.list_models()

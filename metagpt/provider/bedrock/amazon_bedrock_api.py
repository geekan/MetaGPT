
import json
from typing import Literal
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.bedrock.bedrock_provider import get_provider
from metagpt.provider.bedrock.utils import NOT_SUUPORT_STREAM_MODELS, SUPPORT_STREAM_MODELS
import boto3


@register_provider([LLMType.AMAZON_BEDROCK])
class AmazonBedrockLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.__client = self.__init_client("bedrock-runtime")
        self.__provider = get_provider(self.config.model)

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
        client = self.__init_client("bedrock")
        # only output text-generation models
        response = client.list_foundation_models(byOutputModality='TEXT')
        summaries = [f'{summary["modelId"]:50} Support Streaming:{summary["responseStreamingSupported"]}'
                     for summary in response["modelSummaries"]]
        logger.info("\n"+"\n".join(summaries))

    @property
    def _generate_kwargs(self):
        # for now only use temperature due to the difference of request body
        return {
            "temperature": self.config.get("temperature", 0.1),
        }

    def completion(self, messages: list[dict]):
        request_body = self.__provider.get_request_body(
            messages, **self._generate_kwargs)
        response = self.__client.invoke_model(
            modelId=self.config.model, body=request_body
        )
        completions = self.__provider.get_choice_text(response)
        return completions

    def _chat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        if self.config.model in NOT_SUUPORT_STREAM_MODELS:
            logger.warning(
                f"model {self.config.model} doesn't support streaming output!")
            return self.completion(messages)

        request_body = self.__provider.get_request_body(
            messages, **self._generate_kwargs)
        response = self.__client.invoke_model_with_response_stream(
            modelId=self.config.model, body=request_body
        )

        collected_content = []
        for event in response["body"]:
            chunk_text = self.__provider.get_choice_text_from_stream(event)
            collected_content.append(chunk_text)
            log_llm_stream(chunk_text)

        log_llm_stream("\n")
        full_text = ("".join(collected_content)).lstrip()
        return full_text

    async def acompletion(self, messages: list[dict]):
        return self._achat_completion(messages)

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        # TODO:make it async
        return self.completion(messages)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return self._chat_completion_stream(messages)



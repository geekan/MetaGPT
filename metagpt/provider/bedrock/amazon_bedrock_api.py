from typing import Literal
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.bedrock.bedrock_provider import get_provider
from metagpt.provider.bedrock.utils import NOT_SUUPORT_STREAM_MODELS, get_max_tokens
try:
    import boto3
except ImportError:
    raise ImportError(
        "boto3 not found! please install it by `pip install boto3` first ")


@register_provider([LLMType.AMAZON_BEDROCK])
class AmazonBedrockLLM(BaseLLM):
    """
    check out:
    https://docs.aws.amazon.com/code-library/latest/ug/python_3_bedrock-runtime_code_examples.html
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.__client = self.__init_client("bedrock-runtime")
        self.__provider = get_provider(self.config.model)
        logger.warning(
            "Amazon bedrock doesn't support asynchronous calls now")

    def __init_client(self, service_name: Literal["bedrock-runtime", "bedrock"]):
        """initialize boto3 client"""
        # access key and secret key from https://us-east-1.console.aws.amazon.com/iam
        self.__credentital_kwards = {
            "aws_secret_access_key": self.config.secret_key,
            "aws_access_key_id": self.config.access_key,
            "region_name": self.config.region_name
        }
        session = boto3.Session(**self.__credentital_kwards)
        client = session.client(service_name)
        return client

    def list_models(self):
        """list all available text-generation models

        ```shell
        ai21.j2-ultra-v1                    Support Streaming:False
        meta.llama3-70b-instruct-v1:0       Support Streaming:True
        ……
        ```
        """
        client = self.__init_client("bedrock")
        # only output text-generation models
        response = client.list_foundation_models(byOutputModality='TEXT')
        summaries = [f'{summary["modelId"]:50} Support Streaming:{summary["responseStreamingSupported"]}'
                     for summary in response["modelSummaries"]]
        logger.info("\n"+"\n".join(summaries))

    @property
    def _generate_kwargs(self) -> dict:
        model_max_tokens = get_max_tokens(self.config.model)
        if self.config.max_token > model_max_tokens:
            max_tokens = model_max_tokens
        else:
            max_tokens = self.config.max_token

        return {
            self.__provider.max_tokens_field_name: max_tokens,
            "temperature": self.config.temperature
        }

    def completion(self, messages: list[dict]) -> str:
        request_body = self.__provider.get_request_body(
            messages, **self._generate_kwargs)
        response = self.__client.invoke_model(
            modelId=self.config.model, body=request_body
        )
        completions = self.__provider.get_choice_text(response)
        return completions

    def _chat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
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

    # boto3 don't support support asynchronous calls.
    # for asynchronous version of boto3, check out:
    # https://aioboto3.readthedocs.io/en/latest/usage.html
    # However,aioboto3 doesn't support invoke model

    async def acompletion(self, messages: list[dict]):
        return await self._achat_completion(messages)

    async def acompletion_text(self, messages: list[dict], stream: bool = False,
                               timeout: int = USE_CONFIG_TIMEOUT) -> str:
        if stream:
            return await self._achat_completion_stream(messages)
        return await self._achat_completion(messages)

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return self.completion(messages)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return self._chat_completion_stream(messages)

import asyncio
import json
from functools import partial
from typing import List, Literal

import boto3
from botocore.eventstream import EventStream

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.bedrock.bedrock_provider import get_provider
from metagpt.provider.bedrock.utils import NOT_SUUPORT_STREAM_MODELS, get_max_tokens
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import BEDROCK_TOKEN_COSTS


@register_provider([LLMType.BEDROCK])
class BedrockLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.__client = self.__init_client("bedrock-runtime")
        self.__provider = get_provider(self.config.model)
        self.cost_manager = CostManager(token_costs=BEDROCK_TOKEN_COSTS)
        if self.config.model in NOT_SUUPORT_STREAM_MODELS:
            logger.warning(f"model {self.config.model} doesn't support streaming output!")

    def __init_client(self, service_name: Literal["bedrock-runtime", "bedrock"]):
        """initialize boto3 client"""
        # access key and secret key from https://us-east-1.console.aws.amazon.com/iam
        self.__credentital_kwargs = {
            "aws_secret_access_key": self.config.secret_key,
            "aws_access_key_id": self.config.access_key,
            "region_name": self.config.region_name,
        }
        session = boto3.Session(**self.__credentital_kwargs)
        client = session.client(service_name)
        return client

    @property
    def client(self):
        return self.__client

    @property
    def provider(self):
        return self.__provider

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
        response = client.list_foundation_models(byOutputModality="TEXT")
        summaries = [
            f'{summary["modelId"]:50} Support Streaming:{summary["responseStreamingSupported"]}'
            for summary in response["modelSummaries"]
        ]
        logger.info("\n" + "\n".join(summaries))

    async def invoke_model(self, request_body: str) -> dict:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self.client.invoke_model, modelId=self.config.model, body=request_body)
        )
        usage = self._get_usage(response)
        self._update_costs(usage, self.config.model)
        response_body = self._get_response_body(response)
        return response_body

    async def invoke_model_with_response_stream(self, request_body: str) -> EventStream:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self.client.invoke_model_with_response_stream, modelId=self.config.model, body=request_body)
        )
        usage = self._get_usage(response)
        self._update_costs(usage, self.config.model)
        return response

    @property
    def _const_kwargs(self) -> dict:
        model_max_tokens = get_max_tokens(self.config.model)
        if self.config.max_token > model_max_tokens:
            max_tokens = model_max_tokens
        else:
            max_tokens = self.config.max_token

        return {self.__provider.max_tokens_field_name: max_tokens, "temperature": self.config.temperature}

    # boto3 don't support support asynchronous calls.
    # for asynchronous version of boto3, check out:
    # https://aioboto3.readthedocs.io/en/latest/usage.html
    # However,aioboto3 doesn't support invoke model

    def get_choice_text(self, rsp: dict) -> str:
        return self.__provider.get_choice_text(rsp)

    async def acompletion(self, messages: list[dict]) -> dict:
        request_body = self.__provider.get_request_body(messages, self._const_kwargs)
        response_body = await self.invoke_model(request_body)
        return response_body

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self.acompletion(messages)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        if self.config.model in NOT_SUUPORT_STREAM_MODELS:
            rsp = await self.acompletion(messages)
            full_text = self.get_choice_text(rsp)
            log_llm_stream(full_text)
            return full_text

        request_body = self.__provider.get_request_body(messages, self._const_kwargs, stream=True)
        stream_response = await self.invoke_model_with_response_stream(request_body)
        collected_content = await self._get_stream_response_body(stream_response)
        log_llm_stream("\n")
        full_text = ("".join(collected_content)).lstrip()
        return full_text

    def _get_response_body(self, response) -> dict:
        response_body = json.loads(response["body"].read())
        return response_body

    async def _get_stream_response_body(self, stream_response) -> List[str]:
        def collect_content() -> str:
            collected_content = []
            for event in stream_response["body"]:
                chunk_text = self.__provider.get_choice_text_from_stream(event)
                collected_content.append(chunk_text)
                log_llm_stream(chunk_text)
            return collected_content

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, collect_content)

    def _get_usage(self, response) -> dict[str, int]:
        headers = response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        prompt_tokens = int(headers.get("x-amzn-bedrock-input-token-count", 0))
        completion_tokens = int(headers.get("x-amzn-bedrock-output-token-count", 0))
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        return usage

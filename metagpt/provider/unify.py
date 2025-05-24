from typing import Optional, Dict, List, Union
from openai.types import Completion, CompletionUsage
from openai.types.chat import ChatCompletion

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import count_message_tokens, OPENAI_TOKEN_COSTS
from unify.clients import Unify, AsyncUnify

@register_provider([LLMType.UNIFY])
class UnifyLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_client()
        self.cost_manager = CostManager(token_costs=OPENAI_TOKEN_COSTS)  # Using OpenAI costs as Unify is compatible

    def _init_client(self):
        self.model = self.config.model
        self.client = Unify(
            api_key=self.config.api_key,
            endpoint=f"{self.config.model}@{self.config.provider}",
        )
        self.async_client = AsyncUnify(
            api_key=self.config.api_key,
            endpoint=f"{self.config.model}@{self.config.provider}",
        )

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        return {
            "messages": messages,
            "max_tokens": self.config.max_token,
            "temperature": self.config.temperature,
            "stream": stream,
        }

    def get_choice_text(self, resp: Union[ChatCompletion, str]) -> str:
        if isinstance(resp, str):
            return resp
        return resp.choices[0].message.content if resp.choices else ""

    def _update_costs(self, usage: dict):
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        self.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletion:
        try:
            response = await self.async_client.generate(
                messages=messages,
                max_tokens=self.config.max_token,
                temperature=self.config.temperature,
                stream=False,
            )
            # Construct a ChatCompletion object to match OpenAI's format
            chat_completion = ChatCompletion(
                id="unify_chat_completion",
                object="chat.completion",
                created=0,  # Unify doesn't provide this, so we use 0
                model=self.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response,
                    },
                    "finish_reason": "stop",
                }],
                usage=CompletionUsage(
                    prompt_tokens=count_message_tokens(messages, self.model),
                    completion_tokens=count_message_tokens([{"role": "assistant", "content": response}], self.model),
                    total_tokens=0,  # Will be calculated below
                ),
            )
            chat_completion.usage.total_tokens = chat_completion.usage.prompt_tokens + chat_completion.usage.completion_tokens
            self._update_costs(chat_completion.usage.model_dump())
            return chat_completion
        except Exception as e:
            logger.error(f"Error in Unify chat completion: {str(e)}")
            raise

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        try:
            stream = self.client.generate(
                messages=messages,
                max_tokens=self.config.max_token,
                temperature=self.config.temperature,
                stream=True,
            )
            collected_content = []
            for chunk in stream:
                log_llm_stream(chunk)
                collected_content.append(chunk)

            full_content = "".join(collected_content)
            usage = {
                "prompt_tokens": count_message_tokens(messages, self.model),
                "completion_tokens": count_message_tokens([{"role": "assistant", "content": full_content}], self.model),
            }
            self._update_costs(usage)
            return full_content
        except Exception as e:
            logger.error(f"Error in Unify chat completion stream: {str(e)}")
            raise

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletion:
        return await self._achat_completion(messages, timeout=timeout)

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=USE_CONFIG_TIMEOUT) -> str:
        if stream:
            return await self._achat_completion_stream(messages, timeout=timeout)
        response = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(response)

    def get_model_name(self):
        return self.model

    def get_usage(self) -> Optional[Dict[str, int]]:
        return self.cost_manager.get_latest_usage()
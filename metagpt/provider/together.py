import asyncio
from typing import Optional, Union, AsyncGenerator
from together import Together

from metagpt.provider.base_llm import BaseLLM
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import logger
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import count_input_tokens, count_output_tokens, get_max_completion_tokens
from metagpt.utils.exceptions import handle_exception

@register_provider(LLMType.TOGETHER)
class TogetherLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_together()
        self.auto_max_tokens = False
        self.cost_manager: Optional[CostManager] = None

    def _init_together(self):
        self.model = self.config.model
        self.client = Together(api_key=self.config.api_key)
        if self.config.base_url:
            self.client.base_url = self.config.base_url

    def _cons_kwargs(self, messages: list[dict], stream: bool = False, **kwargs) -> dict:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self._get_max_tokens(messages),
            "stream": stream,
        }
        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        kwargs = self._cons_kwargs(messages, timeout=self.get_timeout(timeout))
        response = await asyncio.to_thread(self.client.chat.completions.create, **kwargs)
        self._update_costs(response.usage)
        return response

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> AsyncGenerator[str, None]:
        kwargs = self._cons_kwargs(messages, stream=True, timeout=self.get_timeout(timeout))
        response = await asyncio.to_thread(self.client.chat.completions.create, **kwargs)
        
        collected_messages = []
        current_sentence = ""
        for chunk in response:
            if chunk.choices:
                chunk_message = chunk.choices[0].delta.content
                if chunk_message:
                    current_sentence += chunk_message
                    if chunk_message.endswith(('.', '!', '?', '\n')):
                        collected_messages.append(current_sentence)
                        yield current_sentence
                        print(current_sentence, end='', flush=True)  # Print each sentence as it's completed
                        current_sentence = ""
        
        if current_sentence:
            collected_messages.append(current_sentence)
            yield current_sentence
            print(current_sentence, end='', flush=True)
        
        print()  # Print a newline after the full response
        
        full_content = "".join(collected_messages)
        usage = self._calc_usage(messages, full_content)
        self._update_costs(usage)

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    @handle_exception
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=USE_CONFIG_TIMEOUT) -> str:
        if stream:
            collected_messages = []
            async for chunk in self._achat_completion_stream(messages, timeout=timeout):
                collected_messages.append(chunk)
            return "".join(collected_messages)
        
        response = await self._achat_completion(messages, timeout=self.get_timeout(timeout))
        response_text = self.get_choice_text(response)
        print(f"{messages[-1]['role'].capitalize()}: {response_text}")  # Print the full response
        return response_text

    def _calc_usage(self, messages: list[dict], response_text: str):
        try:
            prompt_tokens = count_input_tokens(messages, self.model)
            completion_tokens = count_output_tokens(response_text, self.model)
        except NotImplementedError:
            # Fallback to a simple estimation method
            prompt_tokens = sum(len(m['content'].split()) for m in messages)
            completion_tokens = len(response_text.split())
            logger.warning(f"Token counting not implemented for {self.model}. Using word count as an estimation.")

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }

    def get_choice_text(self, rsp) -> str:
        return rsp.choices[0].message.content if rsp.choices and rsp.choices[0].message.content else ""

    def _get_max_tokens(self, messages: list[dict]) -> int:
        if not self.auto_max_tokens:
            return self.config.max_token
        try:
            return get_max_completion_tokens(messages, self.model, self.config.max_token)
        except NotImplementedError:
            # Fallback to a simple estimation method
            logger.warning(f"Max token calculation not implemented for {self.model}. Using default max_token.")
            return self.config.max_token

    def _update_costs(self, usage):
        if self.cost_manager:
            try:
                self.cost_manager.update_cost(
                    prompt_tokens=usage['prompt_tokens'],
                    completion_tokens=usage['completion_tokens'],
                    model=self.model
                )
            except Exception as e:
                logger.warning(f"Failed to update costs: {str(e)}")

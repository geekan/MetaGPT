# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : metagpt_llm_api.py
@Desc    : MetaGPT LLM related APIs
"""

from metagpt.provider.openai_api import OpenAIGPTAPI
# from metagpt.provider.base_gpt_api import BaseGPTAPI
# from metagpt.provider.openai_api import RateLimiter


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""
    
    def __init__(self):
        super(MetaGPTLLMAPI, self).__init__()

    # def __init__(self):
    #     self.__init_openai(CONFIG)
    #     self.llm = openai
    #     self.model = CONFIG.openai_api_model
    #     self.auto_max_tokens = False
    #     self._cost_manager = CostManager()
    #     RateLimiter.__init__(self, rpm=self.rpm)
    # 
    # def __init_openai(self, config):
    #     openai.api_key = config.openai_api_key
    #     if config.openai_api_base:
    #         openai.api_base = config.openai_api_base
    #     if config.openai_api_type:
    #         openai.api_type = config.openai_api_type
    #         openai.api_version = config.openai_api_version
    #     self.rpm = int(config.get("RPM", 10))
    # 
    # async def _achat_completion_stream(self, messages: list[dict]) -> str:
    #     response = await openai.ChatCompletion.acreate(**self._cons_kwargs(messages), stream=True)
    # 
    #     # create variables to collect the stream of chunks
    #     collected_chunks = []
    #     collected_messages = []
    #     # iterate through the stream of events
    #     async for chunk in response:
    #         collected_chunks.append(chunk)  # save the event response
    #         choices = chunk["choices"]
    #         if len(choices) > 0:
    #             chunk_message = chunk["choices"][0].get("delta", {})  # extract the message
    #             collected_messages.append(chunk_message)  # save the message
    #             if "content" in chunk_message:
    #                 print(chunk_message["content"], end="")
    #     print()
    # 
    #     full_reply_content = "".join([m.get("content", "") for m in collected_messages])
    #     usage = self._calc_usage(messages, full_reply_content)
    #     self._update_costs(usage)
    #     return full_reply_content
    # 
    # def _cons_kwargs(self, messages: list[dict], **configs) -> dict:
    #     kwargs = {
    #         "messages": messages,
    #         "max_tokens": self.get_max_tokens(messages),
    #         "n": 1,
    #         "stop": None,
    #         "temperature": 0.3,
    #         "timeout": 3,
    #     }
    #     if configs:
    #         kwargs.update(configs)
    # 
    #     if CONFIG.openai_api_type == "azure":
    #         if CONFIG.deployment_name and CONFIG.deployment_id:
    #             raise ValueError("You can only use one of the `deployment_id` or `deployment_name` model")
    #         elif not CONFIG.deployment_name and not CONFIG.deployment_id:
    #             raise ValueError("You must specify `DEPLOYMENT_NAME` or `DEPLOYMENT_ID` parameter")
    #         kwargs_mode = (
    #             {"engine": CONFIG.deployment_name}
    #             if CONFIG.deployment_name
    #             else {"deployment_id": CONFIG.deployment_id}
    #         )
    #     else:
    #         kwargs_mode = {"model": self.model}
    #     kwargs.update(kwargs_mode)
    #     return kwargs
    # 
    # async def _achat_completion(self, messages: list[dict]) -> dict:
    #     rsp = await self.llm.ChatCompletion.acreate(**self._cons_kwargs(messages))
    #     self._update_costs(rsp.get("usage"))
    #     return rsp
    # 
    # def _chat_completion(self, messages: list[dict]) -> dict:
    #     rsp = self.llm.ChatCompletion.create(**self._cons_kwargs(messages))
    #     self._update_costs(rsp)
    #     return rsp
    # 
    # def completion(self, messages: list[dict]) -> dict:
    #     # if isinstance(messages[0], Message):
    #     #     messages = self.messages_to_dict(messages)
    #     return self._chat_completion(messages)
    # 
    # async def acompletion(self, messages: list[dict]) -> dict:
    #     # if isinstance(messages[0], Message):
    #     #     messages = self.messages_to_dict(messages)
    #     return await self._achat_completion(messages)
    # 
    # @retry(
    #     wait=wait_random_exponential(min=1, max=60),
    #     stop=stop_after_attempt(6),
    #     after=after_log(logger, logger.level("WARNING").name),
    #     retry=retry_if_exception_type(APIConnectionError),
    #     retry_error_callback=log_and_reraise,
    # )
    # async def acompletion_text(self, messages: list[dict], stream=False) -> str:
    #     """when streaming, print each token in place."""
    #     if stream:
    #         return await self._achat_completion_stream(messages)
    #     rsp = await self._achat_completion(messages)
    #     return self.get_choice_text(rsp)
    # 
    # def _func_configs(self, messages: list[dict], **kwargs) -> dict:
    #     """
    #     Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create
    #     """
    #     if "tools" not in kwargs:
    #         configs = {
    #             "tools": [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}],
    #             "tool_choice": GENERAL_TOOL_CHOICE,
    #         }
    #         kwargs.update(configs)
    # 
    #     return self._cons_kwargs(messages, **kwargs)
    # 
    # def _chat_completion_function(self, messages: list[dict], **kwargs) -> dict:
    #     rsp = self.llm.ChatCompletion.create(**self._func_configs(messages, **kwargs))
    #     self._update_costs(rsp.get("usage"))
    #     return rsp
    # 
    # async def _achat_completion_function(self, messages: list[dict], **chat_configs) -> dict:
    #     rsp = await self.llm.ChatCompletion.acreate(**self._func_configs(messages, **chat_configs))
    #     self._update_costs(rsp.get("usage"))
    #     return rsp
    # 
    # def _process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
    #     """convert messages to list[dict]."""
    #     if isinstance(messages, list):
    #         messages = [Message(msg) if isinstance(msg, str) else msg for msg in messages]
    #         return [msg if isinstance(msg, dict) else msg.to_dict() for msg in messages]
    # 
    #     if isinstance(messages, Message):
    #         messages = [messages.to_dict()]
    #     elif isinstance(messages, str):
    #         messages = [{"role": "user", "content": messages}]
    #     else:
    #         raise ValueError(
    #             f"Only support messages type are: str, Message, list[dict], but got {type(messages).__name__}!"
    #         )
    #     return messages
    # 
    # def ask_code(self, messages: Union[str, Message, list[dict]], **kwargs) -> dict:
    #     """Use function of tools to ask a code.
    # 
    #     Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create
    # 
    #     Examples:
    # 
    #     >>> llm = OpenAIGPTAPI()
    #     >>> llm.ask_code("Write a python hello world code.")
    #     {'language': 'python', 'code': "print('Hello, World!')"}
    #     >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
    #     >>> llm.ask_code(msg)
    #     {'language': 'python', 'code': "print('Hello, World!')"}
    #     """
    #     messages = self._process_message(messages)
    #     rsp = self._chat_completion_function(messages, **kwargs)
    #     return self.get_choice_function_arguments(rsp)
    # 
    # async def aask_code(self, messages: Union[str, Message, list[dict]], **kwargs) -> dict:
    #     """Use function of tools to ask a code.
    # 
    #     Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create
    # 
    #     Examples:
    # 
    #     >>> llm = OpenAIGPTAPI()
    #     >>> rsp = await llm.ask_code("Write a python hello world code.")
    #     >>> rsp
    #     {'language': 'python', 'code': "print('Hello, World!')"}
    #     >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
    #     >>> rsp = await llm.aask_code(msg)   # -> {'language': 'python', 'code': "print('Hello, World!')"}
    #     """
    #     messages = self._process_message(messages)
    #     rsp = await self._achat_completion_function(messages, **kwargs)
    #     return self.get_choice_function_arguments(rsp)
    # 
    # def _calc_usage(self, messages: list[dict], rsp: str) -> dict:
    #     usage = {}
    #     if CONFIG.calc_usage:
    #         try:
    #             prompt_tokens = count_message_tokens(messages, self.model)
    #             completion_tokens = count_string_tokens(rsp, self.model)
    #             usage["prompt_tokens"] = prompt_tokens
    #             usage["completion_tokens"] = completion_tokens
    #             return usage
    #         except Exception as e:
    #             logger.error("usage calculation failed!", e)
    #     else:
    #         return usage
    # 
    # async def acompletion_batch(self, batch: list[list[dict]]) -> list[dict]:
    #     """Return full JSON"""
    #     split_batches = self.split_batches(batch)
    #     all_results = []
    # 
    #     for small_batch in split_batches:
    #         logger.info(small_batch)
    #         await self.wait_if_needed(len(small_batch))
    # 
    #         future = [self.acompletion(prompt) for prompt in small_batch]
    #         results = await asyncio.gather(*future)
    #         logger.info(results)
    #         all_results.extend(results)
    # 
    #     return all_results
    # 
    # async def acompletion_batch_text(self, batch: list[list[dict]]) -> list[str]:
    #     """Only return plain text"""
    #     raw_results = await self.acompletion_batch(batch)
    #     results = []
    #     for idx, raw_result in enumerate(raw_results, start=1):
    #         result = self.get_choice_text(raw_result)
    #         results.append(result)
    #         logger.info(f"Result of task {idx}: {result}")
    #     return results
    # 
    # def _update_costs(self, usage: dict):
    #     if CONFIG.calc_usage:
    #         try:
    #             prompt_tokens = int(usage["prompt_tokens"])
    #             completion_tokens = int(usage["completion_tokens"])
    #             self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
    #         except Exception as e:
    #             logger.error("updating costs failed!", e)
    # 
    # def get_costs(self) -> Costs:
    #     return self._cost_manager.get_costs()
    # 
    # def get_max_tokens(self, messages: list[dict]):
    #     if not self.auto_max_tokens:
    #         return CONFIG.max_tokens_rsp
    #     return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)
    # 
    # def moderation(self, content: Union[str, list[str]]):
    #     try:
    #         if not content:
    #             logger.error("content cannot be empty!")
    #         else:
    #             rsp = self._moderation(content=content)
    #             return rsp
    #     except Exception as e:
    #         logger.error(f"moderating failed:{e}")
    # 
    # def _moderation(self, content: Union[str, list[str]]):
    #     rsp = self.llm.Moderation.create(input=content)
    #     return rsp
    # 
    # async def amoderation(self, content: Union[str, list[str]]):
    #     try:
    #         if not content:
    #             logger.error("content cannot be empty!")
    #         else:
    #             rsp = await self._amoderation(content=content)
    #             return rsp
    #     except Exception as e:
    #         logger.error(f"moderating failed:{e}")
    # 
    # async def _amoderation(self, content: Union[str, list[str]]):
    #     rsp = await self.llm.Moderation.acreate(input=content)
    #     return rsp

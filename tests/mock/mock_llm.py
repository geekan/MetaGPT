from typing import Optional

from metagpt.logs import log_llm_stream, logger
from metagpt.provider.openai_api import OpenAILLM


class MockLLM(OpenAILLM):
    def __init__(self):
        super().__init__()
        self.rsp_cache: dict = {}
        self.rsp_candidates: list[dict] = []  # a test can have multiple calls with the same llm, thus a list

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """Overwrite original acompletion_text to cancel retry"""
        if stream:
            resp = self._achat_completion_stream(messages, timeout=timeout)

            collected_messages = []
            async for i in resp:
                log_llm_stream(i)
                collected_messages.append(i)

            full_reply_content = "".join(collected_messages)
            usage = self._calc_usage(messages, full_reply_content)
            self._update_costs(usage)
            return full_reply_content

        rsp = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(rsp)

    async def original_aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        timeout=3,
        stream=True,
    ):
        """A copy of metagpt.provider.base_llm.BaseLLM.aask, we can't use super().aask because it will be mocked"""
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()] if self.use_system_prompt else []
        if format_msgs:
            message.extend(format_msgs)
        message.append(self._user_msg(msg))
        rsp = await self.acompletion_text(message, stream=stream, timeout=timeout)
        return rsp

    async def original_aask_batch(self, msgs: list, timeout=3) -> str:
        """A copy of metagpt.provider.base_llm.BaseLLM.aask_batch, we can't use super().aask because it will be mocked"""
        context = []
        for msg in msgs:
            umsg = self._user_msg(msg)
            context.append(umsg)
            rsp_text = await self.acompletion_text(context, timeout=timeout)
            context.append(self._assistant_msg(rsp_text))
        return self._extract_assistant_rsp(context)

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        timeout=3,
        stream=True,
    ) -> str:
        if msg not in self.rsp_cache:
            # Call the original unmocked method
            rsp = await self.original_aask(msg, system_msgs, format_msgs, timeout, stream)
            logger.info(f"Added '{rsp[:20]} ...' to response cache")
            self.rsp_candidates.append({msg: rsp})
            return rsp
        else:
            logger.warning("Use response cache")
            return self.rsp_cache[msg]

    async def aask_batch(self, msgs: list, timeout=3) -> str:
        joined_msgs = "#MSG_SEP#".join([msg if isinstance(msg, str) else msg.content for msg in msgs])
        if joined_msgs not in self.rsp_cache:
            # Call the original unmocked method
            rsp = await self.original_aask_batch(msgs, timeout)
            logger.info(f"Added '{joined_msgs[:20]} ...' to response cache")
            self.rsp_candidates.append({joined_msgs: rsp})
            return rsp
        else:
            logger.warning("Use response cache")
            return self.rsp_cache[joined_msgs]

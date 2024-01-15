#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:04
@Author  : alexanderwu
@File    : base_llm.py
@Desc    : mashenquan, 2023/8/22. + try catch
"""
import re
import json
from abc import ABC, abstractmethod
from typing import Optional

from metagpt.logs import logger
from metagpt.utils.common import CodeParser


class BaseLLM(ABC):
    """LLM API abstract class, requiring all inheritors to provide a series of standard capabilities"""

    use_system_prompt: bool = True
    system_prompt = "You are a helpful assistant."

    def _user_msg(self, msg: str) -> dict[str, str]:
        return {"role": "user", "content": msg}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "assistant", "content": msg}

    def _system_msg(self, msg: str) -> dict[str, str]:
        return {"role": "system", "content": msg}

    def _system_msgs(self, msgs: list[str]) -> list[dict[str, str]]:
        return [self._system_msg(msg) for msg in msgs]

    def _default_system_msg(self):
        return self._system_msg(self.system_prompt)

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        timeout=3,
        stream=True,
    ) -> str:
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()] if self.use_system_prompt else []
        if format_msgs:
            message.extend(format_msgs)
        message.append(self._user_msg(msg))
        rsp = await self.acompletion_text(message, stream=stream, timeout=timeout)
        return rsp

    def _extract_assistant_rsp(self, context):
        return "\n".join([i["content"] for i in context if i["role"] == "assistant"])

    async def aask_batch(self, msgs: list, timeout=3) -> str:
        """Sequential questioning"""
        context = []
        for msg in msgs:
            umsg = self._user_msg(msg)
            context.append(umsg)
            rsp_text = await self.acompletion_text(context, timeout=timeout)
            context.append(self._assistant_msg(rsp_text))
        return self._extract_assistant_rsp(context)

    async def aask_code(self, msgs: list[str], timeout=3) -> str:
        """FIXME: No code segment filtering has been done here, and all results are actually displayed"""
        rsp_text = await self.aask_batch(msgs, timeout=timeout)
        return rsp_text

    @abstractmethod
    async def acompletion(self, messages: list[dict], timeout=3):
        """Asynchronous version of completion
        All GPTAPIs are required to provide the standard OpenAI completion interface
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "hello, show me python hello world code"},
            # {"role": "assistant", "content": ...}, # If there is an answer in the history, also include it
        ]
        """

    @abstractmethod
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """Asynchronous version of completion. Return str. Support stream-print"""

    def get_choice_text(self, rsp: dict) -> str:
        """Required to provide the first text of choice"""
        return rsp.get("choices")[0]["message"]["content"]

    def get_choice_function(self, rsp: dict) -> dict:
        """Required to provide the first function of choice
        :param dict rsp: OpenAI chat.comletion respond JSON, Note "message" must include "tool_calls",
            and "tool_calls" must include "function", for example:
            {...
                "choices": [
                    {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": null,
                        "tool_calls": [
                        {
                            "id": "call_Y5r6Ddr2Qc2ZrqgfwzPX5l72",
                            "type": "function",
                            "function": {
                            "name": "execute",
                            "arguments": "{\n  \"language\": \"python\",\n  \"code\": \"print('Hello, World!')\"\n}"
                            }
                        }
                        ]
                    },
                    "finish_reason": "stop"
                    }
                ],
                ...}
        :return dict: return first function of choice, for exmaple,
            {'name': 'execute', 'arguments': '{\n  "language": "python",\n  "code": "print(\'Hello, World!\')"\n}'}
        """
        return rsp.get("choices")[0]["message"]["tool_calls"][0]["function"]

    def _parse_arguments(self, arguments: str) -> dict:
        """parse arguments in openai function call"""
        if 'langugae' not in arguments and 'code' not in arguments:
            logger.warning(f"Not found `code`, `language`, We assume it is pure code:\n {arguments}\n. ")
            return {'language': 'python', 'code': arguments}

        # 匹配language
        language_pattern = re.compile(r'[\"\']?language[\"\']?\s*:\s*["\']([^"\']+?)["\']', re.DOTALL)
        language_match = language_pattern.search(arguments)
        language_value = language_match.group(1) if language_match else None

        # 匹配code
        code_pattern = r'(["\']{3}|["])([\s\S]*?)\1'
        try:
            code_value = re.findall(code_pattern, arguments)[-1][-1]
        except Exception as e:
            logger.error(f"{e}, when re.findall({code_pattern}, {arguments})")
            code_value = None

        if code_value is None:
            raise ValueError(f"Parse code error for {arguments}")
        # arguments只有code的情况
        return {'language': language_value, 'code': code_value}

    def get_choice_function_arguments(self, rsp: dict) -> dict:
        """Required to provide the first function arguments of choice.

        :param dict rsp: same as in self.get_choice_function(rsp)
        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        try:
            arguments: str = self.get_choice_function(rsp)["arguments"]
            return json.loads(arguments, strict=False)
        except json.decoder.JSONDecodeError as e:
            logger.debug(f"Got JSONDecodeError for {arguments}, we will use RegExp to parse code, \n {e}")
            return self._parse_arguments(arguments)
        except KeyError as e:
            if 'tool_calls' in e.args:
                txt_rsp = self.get_choice_text(rsp)
                # find code
                code = CodeParser.parse_code(None, txt_rsp, lang='python')
                if code != txt_rsp:
                    return {'language': 'python', 'code': code}
                # no code
                return {'language': 'markdown', 'code': txt_rsp}
            raise e
        except Exception as e:
            logger.error(f"Got error `{e}` for parsing\n {rsp}\n")
            return {}

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])

    def messages_to_dict(self, messages):
        """objects to [{"role": "user", "content": msg}] etc."""
        return [i.to_dict() for i in messages]

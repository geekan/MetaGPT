"""
说明：
"""
import asyncio
from typing import Optional

import zhipuai

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI


class ChatglmAPI(BaseGPTAPI):
    def __init__(self):
        logger.info(CONFIG.chatglm_api_key)
        zhipuai.api_key = CONFIG.chatglm_api_key

    def completion(self, messages: list[dict]):
        response = zhipuai.model_api.sse_invoke(
            model="chatglm_turbo",
            prompt=messages,
            temperature=0.95,
            top_p=0.7,
            incremental=True
        )
        ret = ''
        for event in response.events():
            if event.event == "add":
                ret += event.data
                # 我不知道这里怎么禁止输出换行
                print(event.data, end='')
            elif event.event == "error" or event.event == "interrupted":
                logger.error(event.data)
            elif event.event == "finish":
                logger.info(event.data)
                # logger.info(event.meta)
            else:
                logger.info(event.data)
        return ret

    async def acompletion(self, messages: list[dict]):
        response = zhipuai.model_api.async_invoke(
            model="chatglm_turbo",
            prompt=messages
        )
        task_id = response['data']['task_id']
        while True:
            await asyncio.sleep(1)
            result = zhipuai.model_api.query_async_invoke_result(task_id)
            if result['data']['task_status'] == "SUCCESS":
                answer = result['data']['choices'][0]['content']
                return answer

    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        # 不支持同时异步运行和输出内容，因为不可能同时流式输出两份内容
        if stream:
            return self.completion(messages)
        return await self.acompletion(messages)

    def get_choice_text(self, rsp: dict) -> str:
        """Required to provide the first text of choice"""
        return rsp['data']['choices'][0]['content']

    def ask(self, msg: str) -> str:
        message = [self._user_msg(msg)]
        rsp = self.completion(message)
        return self.get_choice_text(rsp)

    async def aask(self, msg: str, system_msgs: Optional[list[str]] = None) -> str:
        if system_msgs:
            message = self._system_msgs(system_msgs) + [self._user_msg(msg)]
        else:
            message = self._user_msg(msg)
        rsp = await self.acompletion_text(message, stream=False)
        logger.debug(message)
        # logger.debug(rsp)
        return rsp


if __name__ == '__main__':
    # run the tasks
    llm = ChatglmAPI()
    message = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "我是人工智能助手"},
        {"role": "user", "content": "你叫什么名字"},
        {"role": "assistant", "content": "我叫chatGLM"},
        {"role": "user", "content": "你都可以做些什么事"},
    ]
    logger.info(asyncio.run(llm.aask("你都可以做些什么事", {})))

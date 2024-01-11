#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : spark_api.py
"""
import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import ssl
from time import mktime
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

import websocket  # 使用websocket_client

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider


@register_provider(LLMType.SPARK)
class SparkLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        logger.warning("SparkLLM：当前方法无法支持异步运行。当你使用acompletion时，并不能并行访问。")

    def get_choice_text(self, rsp: dict) -> str:
        return rsp["payload"]["choices"]["text"][-1]["content"]

    async def acompletion_text(self, messages: list[dict], stream=False, timeout: int = 3) -> str:
        # 不支持
        # logger.warning("当前方法无法支持异步运行。当你使用acompletion时，并不能并行访问。")
        w = GetMessageFromWeb(messages, self.config)
        return w.run()

    async def acompletion(self, messages: list[dict], timeout=3):
        # 不支持异步
        w = GetMessageFromWeb(messages, self.config)
        return w.run()


class GetMessageFromWeb:
    class WsParam:
        """
        该类适合讯飞星火大部分接口的调用。
        输入 app_id, api_key, api_secret, spark_url以初始化，
        create_url方法返回接口url
        """

        # 初始化
        def __init__(self, app_id, api_key, api_secret, spark_url, message=None):
            self.app_id = app_id
            self.api_key = api_key
            self.api_secret = api_secret
            self.host = urlparse(spark_url).netloc
            self.path = urlparse(spark_url).path
            self.spark_url = spark_url
            self.message = message

        # 生成url
        def create_url(self):
            # 生成RFC1123格式的时间戳
            now = datetime.datetime.now()
            date = format_date_time(mktime(now.timetuple()))

            # 拼接字符串
            signature_origin = "host: " + self.host + "\n"
            signature_origin += "date: " + date + "\n"
            signature_origin += "GET " + self.path + " HTTP/1.1"

            # 进行hmac-sha256进行加密
            signature_sha = hmac.new(
                self.api_secret.encode("utf-8"), signature_origin.encode("utf-8"), digestmod=hashlib.sha256
            ).digest()

            signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding="utf-8")

            authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

            authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(encoding="utf-8")

            # 将请求的鉴权参数组合为字典
            v = {"authorization": authorization, "date": date, "host": self.host}
            # 拼接鉴权参数，生成url
            url = self.spark_url + "?" + urlencode(v)
            # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
            return url

    def __init__(self, text, config: LLMConfig):
        self.text = text
        self.ret = ""
        self.spark_appid = config.app_id
        self.spark_api_secret = config.api_secret
        self.spark_api_key = config.api_key
        self.domain = config.domain
        self.spark_url = config.base_url

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data["header"]["code"]

        if code != 0:
            ws.close()  # 请求错误，则关闭socket
            logger.critical(f"回答获取失败，响应信息反序列化之后为： {data}")
            return
        else:
            choices = data["payload"]["choices"]
            # seq = choices["seq"]  # 服务端是流式返回，seq为返回的数据序号
            status = choices["status"]  # 服务端是流式返回，status用于判断信息是否传送完毕
            content = choices["text"][0]["content"]  # 本次接收到的回答文本
            self.ret += content
            if status == 2:
                ws.close()

    # 收到websocket错误的处理
    def on_error(self, ws, error):
        # on_message方法处理接收到的信息，出现任何错误，都会调用这个方法
        logger.critical(f"通讯连接出错，【错误提示: {error}】")

    # 收到websocket关闭的处理
    def on_close(self, ws, one, two):
        pass

    # 处理请求数据
    def gen_params(self):
        data = {
            "header": {"app_id": self.spark_appid, "uid": "1234"},
            "parameter": {
                "chat": {
                    # domain为必传参数
                    "domain": self.domain,
                    # 以下为可微调，非必传参数
                    # 注意：官方建议，temperature和top_k修改一个即可
                    "max_tokens": 2048,  # 默认2048，模型回答的tokens的最大长度，即允许它输出文本的最长字数
                    "temperature": 0.5,  # 取值为[0,1],默认为0.5。取值越高随机性越强、发散性越高，即相同的问题得到的不同答案的可能性越高
                    "top_k": 4,  # 取值为[1，6],默认为4。从k个候选中随机选择一个（非等概率）
                }
            },
            "payload": {"message": {"text": self.text}},
        }
        return data

    def send(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 收到websocket连接建立的处理
    def on_open(self, ws):
        thread.start_new_thread(self.send, (ws,))

    # 处理收到的 websocket消息，出现任何错误，调用on_error方法
    def run(self):
        return self._run(self.text)

    def _run(self, text_list):
        ws_param = self.WsParam(self.spark_appid, self.spark_api_key, self.spark_api_secret, self.spark_url, text_list)
        ws_url = ws_param.create_url()

        websocket.enableTrace(False)  # 默认禁用 WebSocket 的跟踪功能
        ws = websocket.WebSocketApp(
            ws_url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close, on_open=self.on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.ret

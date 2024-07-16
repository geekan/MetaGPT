# -*- coding: utf-8 -*-
# @Time    : 2024/3/27 10:00
# @Author  : leiwu30
# @File    : stream_pipe.py
# @Version : None
# @Description : None

import json
import time
from multiprocessing import Pipe


class StreamPipe:
    def __init__(self, name=None):
        self.name = name
        self.parent_conn, self.child_conn = Pipe()
        self.finish: bool = False

    format_data = {
        "id": "chatcmpl-96bVnBOOyPFZZxEoTIGbdpFcVEnur",
        "object": "chat.completion.chunk",
        "created": 1711361191,
        "model": "gpt-3.5-turbo-0125",
        "system_fingerprint": "fp_3bc1b5746c",
        "choices": [
            {"index": 0, "delta": {"role": "assistant", "content": "content"}, "logprobs": None, "finish_reason": None}
        ],
    }

    def set_message(self, msg):
        self.parent_conn.send(msg)

    def get_message(self, timeout: int = 3):
        if self.child_conn.poll(timeout):
            return self.child_conn.recv()
        else:
            return None

    def msg2stream(self, msg):
        self.format_data["created"] = int(time.time())
        self.format_data["choices"][0]["delta"]["content"] = msg
        return f"data: {json.dumps(self.format_data, ensure_ascii=False)}\n".encode("utf-8")

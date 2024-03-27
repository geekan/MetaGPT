# -*- coding: utf-8 -*-
# @Time    : 2024/3/27 10:00
# @Author  : leiwu30 
# @File    : stream_pipe.py
# @Version : None
# @Description : None

import time
import json
from multiprocessing import Pipe


class StreamPipe:
    parent_conn, child_conn = Pipe()

    variable: list = {}
    finish: bool = False

    format_data = {
        "id": "chatcmpl-96bVnBOOyPFZZxEoTIGbdpFcVEnur",
        "object": "chat.completion.chunk",
        "created": 1711361191,
        "model": "gpt-3.5-turbo-0125",
        "system_fingerprint": "fp_3bc1b5746c",
        "choices": [
            {
                "index": 0,
                "delta":
                    {
                        "role": "assistant",
                        "content": "content"
                    },
                "logprobs": None,
             "finish_reason": None
            }
        ]
    }

    def set_message(self, msg):
        self.parent_conn.send(msg)

    def wait(self):
        pass

    def get_message(self):
        if self.child_conn.poll(timeout=3):
            return self.child_conn.recv()
        else:
            return None

    def set_k_message(self, k, msg):
        self.variable[k] = msg

    def get_k_message(self, k):
        return self.variable[k]

    def msg2stream(self, msg):
        self.format_data['created'] = int(time.time())
        self.format_data['choices'][0]['delta']['content'] = msg
        return f"data: {json.dumps(self.format_data, ensure_ascii=False)}\n".encode("utf-8")

    def with_finish(self, timeout: int = 3):
        """
        Args:
            timeout: /s
        """
        # Pipe is not empty waiting for pipe condition
        # while self.child_conn.poll(timeout=timeout):
        #     time.sleep(0.5)
        self.finish = True

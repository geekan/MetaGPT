#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/27 9:44
@Author  : leiwu30
@File    : flask_web_api.py
@Description    : Stream log information and communicate over the network via web api.
"""
import os
import json
import socket
import asyncio
import threading

from metagpt.team import Team
from metagpt.const import METAGPT_ROOT
from metagpt.logs import set_llm_stream_logfunc
from metagpt.utils.stream_pipe import StreamPipe
from metagpt.roles.tutorial_assistant import TutorialAssistant

from contextvars import ContextVar
from flask import Flask, Response
from flask import request, jsonify, send_from_directory

app = Flask(__name__)


def stream_pipe_log(content):
    print(content, end="")
    stream_pipe = stream_pipe_var.get(None)
    if stream_pipe:
        stream_pipe.set_message(content)


def write_tutorial(message):
    async def main(idea, stream_pipe):
        stream_pipe_var.set(stream_pipe)
        role = TutorialAssistant(stream_pipe=stream_pipe)
        await role.run(idea)

    def thread_run(idea: str, stream_pipe: StreamPipe = None):
        """
            Convert asynchronous function to thread function
        """
        asyncio.run(main(idea, stream_pipe))

    stream_pipe = StreamPipe()
    thread = threading.Thread(target=thread_run, args=(message["content"], stream_pipe,))
    thread.start()

    while thread.is_alive():
        msg = stream_pipe.get_message()
        yield stream_pipe.msg2stream(msg)

    # 文件位置
    # md_file = stream_pipe.get_k_message("file_name")
    # yield stream_pipe.msg2stream(
    #     f"\n\n[{os.path.basename(md_file)}](http://{server_address}:{server_port}/download/{md_file})")


@app.route('/v1/chat/completions', methods=['POST'])
def completions():
    """
    data: {
        "model": "write_tutorial",
        "stream": true,
        "messages": [
            {
                "role": "user",
                "content": "Write a tutorial about MySQL"
            }
        ]
    }
    """

    data = json.loads(request.data)
    print(json.dumps(data, indent=4, ensure_ascii=False))

    # Non-streaming interfaces are not supported yet
    stream_type = True if "stream" in data.keys() and data["stream"] else False
    if not stream_type:
        return jsonify({"status": 200})

    # Only accept the last user information
    last_message = data["messages"][-1]
    model = data["model"]

    # write_tutorial
    if model == "write_tutorial":
        return Response(write_tutorial(last_message), mimetype="text/plain")
    else:
        return jsonify({"status": 200})
    # return Response(event_stream(), mimetype="text/plain")


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(METAGPT_ROOT, filename, as_attachment=True)


if __name__ == "__main__":
    """
    curl https://$server_address:$server_port/v1/chat/completions -X POST -d '{
        "model": "write_tutorial",
        "stream": true,
        "messages": [
          {
               "role": "user",
               "content": "Write a tutorial about MySQL"
          }
        ]
    }'
    """
    server_port = 7860
    server_address = socket.gethostbyname(socket.gethostname())

    set_llm_stream_logfunc(stream_pipe_log)
    stream_pipe_var: ContextVar[StreamPipe] = ContextVar("stream_pipe")
    app.run(port=server_port, host=server_address)

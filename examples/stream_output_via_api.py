#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/27 9:44
@Author  : leiwu30
@File    : stream_output_via_api.py
@Description    : Stream log information and communicate over the network via web api.
"""
import asyncio
import json
import socket
import threading
from contextvars import ContextVar

from flask import Flask, Response, jsonify, request, send_from_directory

from metagpt.const import TUTORIAL_PATH
from metagpt.logs import logger, set_llm_stream_logfunc
from metagpt.roles.tutorial_assistant import TutorialAssistant
from metagpt.utils.stream_pipe import StreamPipe

app = Flask(__name__)


def stream_pipe_log(content):
    print(content, end="")
    stream_pipe = stream_pipe_var.get(None)
    if stream_pipe:
        stream_pipe.set_message(content)


def write_tutorial(message):
    async def main(idea, stream_pipe):
        stream_pipe_var.set(stream_pipe)
        role = TutorialAssistant()
        await role.run(idea)

    def thread_run(idea: str, stream_pipe: StreamPipe = None):
        """
        Convert asynchronous function to thread function
        """
        asyncio.run(main(idea, stream_pipe))

    stream_pipe = StreamPipe()
    thread = threading.Thread(
        target=thread_run,
        args=(
            message["content"],
            stream_pipe,
        ),
    )
    thread.start()

    while thread.is_alive():
        msg = stream_pipe.get_message()
        yield stream_pipe.msg2stream(msg)


@app.route("/v1/chat/completions", methods=["POST"])
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
    logger.info(json.dumps(data, indent=4, ensure_ascii=False))

    # Non-streaming interfaces are not supported yet
    stream_type = True if data.get("stream") else False
    if not stream_type:
        return jsonify({"status": 400, "msg": "Non-streaming requests are not supported, please use `stream=True`."})

    # Only accept the last user information
    # openai['model'] ~ MetaGPT['agent']
    last_message = data["messages"][-1]
    model = data["model"]

    # write_tutorial
    if model == "write_tutorial":
        return Response(write_tutorial(last_message), mimetype="text/plain")
    else:
        return jsonify({"status": 400, "msg": "No suitable agent found."})


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(TUTORIAL_PATH, filename, as_attachment=True)


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

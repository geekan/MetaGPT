#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/7/26 19:25
@Author  : yingfeng
@File    : stream_response.py
"""
import asyncio
import json
from asyncio import CancelledError, Queue
from contextvars import ContextVar

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse

from metagpt.logs import logger, set_llm_stream_logfunc
from metagpt.roles.tutorial_assistant import TutorialAssistant

app = FastAPI()

context_var: ContextVar[Queue] = ContextVar("context_var")


def stream_log(content):
    if not content:
        return
    print(content, end="")
    queue = context_var.get()
    if queue:
        queue.put_nowait(content)


async def write_task(queue: Queue, prompt: str):
    context_var.set(queue)
    print("Tutorial Assistant is running")
    role = TutorialAssistant()
    await role.run(prompt)
    await queue.put(None)


class TutorialParameter(BaseModel):
    prompt: str = Field(default="Write a tutorial about MySQL", description="The prompt for the tutorial")


@app.get("/api/v1/write_tutorial")
async def write_tutorial(parameter: TutorialParameter):
    queue = Queue()
    asyncio.create_task(write_task(queue, parameter.prompt))

    async def event_generator():
        try:
            while True:
                content = await queue.get()
                if not content:
                    print("Tutorial Assistant is done")
                    break
                data = json.dumps({"data": content}, ensure_ascii=False)
                yield data
        except CancelledError:
            print("connection closed")
        except Exception as e:
            logger.error(f"Server error: {e}")
            yield json.dumps({"data": "server error"}, ensure_ascii=False)

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    set_llm_stream_logfunc(stream_log)
    uvicorn.run(app, host="0.0.0.0", port=8080)

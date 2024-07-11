import asyncio
import threading
import queue as sync_queue
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import uvicorn
from metagpt.llm import LLM

from metagpt.roles.di.data_interpreter import DataInterpreter

app = FastAPI()
llm = LLM()
async def generate_async_stream(queue):
    requirement = "解决这个数学问题：正整数m和n的最大公约数是6。m和n的最小公倍数是126。m + n的最小可能值是多少？"
    await llm.aask(requirement, stream=True, queue=queue)

@app.get("/stream")
def stream():
    queue = sync_queue.Queue()
    print(queue)

    def run_loop(queue):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(generate_async_stream(queue))

    thread = threading.Thread(target=run_loop, args=(queue,))
    thread.start()

    def generate_sync_stream():
        while True:
            message = queue.get()
            print(message)
            if message is None:
                break
            yield f"data: {message}\n\n"

    return EventSourceResponse(generate_sync_stream(), media_type='text/event-stream')

if __name__ == "__main__":
    uvicorn.run(app='examples.ping:app',
                host="0.0.0.0",
                port=3000)

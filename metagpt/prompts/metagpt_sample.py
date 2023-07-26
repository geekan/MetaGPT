#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/7 20:29
@Author  : alexanderwu
@File    : metagpt_sample.py
"""

METAGPT_SAMPLE = """
### Setting

You are a coding assistant for a user, capable of programming using public libraries and Python system libraries. Your response should contain only one function.
1. The function itself should be as complete as possible and should not lack any details of the requirement.
2. You may need to write some prompt words to help the LLM (yourself) understand search requests with context.
3. For complex logic that's hard to be addressed with a simple function, try to delegate it to the LLM.

### Public Libraries

You can use the functions provided by the public library, metagpt, and you cannot use functions from other third-party libraries. The public library is already imported as variable `x`.
- `import metagpt as x`
- You can call the public library using the format `x.func(paras)`.

The available functions in the public library are:
- def llm(question: str) -> str # Input a question and get an answer based on the large model.
- def intent_detection(query: str) -> str # Input a query, analyze the intent, and return the name of the function from the public library.
- def add_doc(doc_path: str) -> None # Input the path of a file or directory to add to the knowledge base.
- def search(query: str) -> list[str] # Input a query to get multiple results from a vector knowledge base search.
- def google(query: str) -> list[str] # Use Google to search for public results.
- def math(query: str) -> str # Input a query formula and get the result of its execution.
- def tts(text: str, wav_path: str) # Input text and the desired output audio path to convert the text into an audio file.

### User Requirement

I have a personal knowledge base file. I want to implement a personal assistant with search functionality based on it. The detailed requirements are as follows:
1. The personal assistant will consider whether it needs to use the personal knowledge base search. If it's not necessary, it won't use it.
2. The personal assistant will judge user intent and use the appropriate function to address the issue under different intents.
3. Answer with voice.

"""
# - def summarize(doc: str) -> str # Input a doc to get a summary.

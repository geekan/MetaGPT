#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/19 23:07
@Author  : alexanderwu
@File    : summarize.py
"""

# From the plugin: ChatGPT - Website and YouTube Video Summaries
# https://chrome.google.com/webstore/detail/chatgpt-%C2%BB-summarize-every/cbgecfllfhmmnknmamkejadjmnmpfjmp?hl=en&utm_source=chrome-ntp-launcher
SUMMARIZE_PROMPT = """
Your output should use the following template:
### Summary
### Facts
- [Emoji] Bulletpoint

Your task is to summarize the text I give you in up to seven concise bullet points and start with a short, high-quality 
summary. Pick a suitable emoji for every bullet point. Your response should be in {{SELECTED_LANGUAGE}}. If the provided
 URL is functional and not a YouTube video, use the text from the {{URL}}. However, if the URL is not functional or is 
a YouTube video, use the following text: {{CONTENT}}.
"""


# GCP-VertexAI-Text Summarization (SUMMARIZE_PROMPT_2-5 are from this source)
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/prompt-design/text_summarization.ipynb
# Long documents require a map-reduce process, see the following notebook
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/document-summarization/summarization_large_documents.ipynb
SUMMARIZE_PROMPT_2 = """
Provide a very short summary, no more than three sentences, for the following article:

Our quantum computers work by manipulating qubits in an orchestrated fashion that we call quantum algorithms.
The challenge is that qubits are so sensitive that even stray light can cause calculation errors — and the problem worsens as quantum computers grow.
This has significant consequences, since the best quantum algorithms that we know for running useful applications require the error rates of our qubits to be far lower than we have today.
To bridge this gap, we will need quantum error correction.
Quantum error correction protects information by encoding it across multiple physical qubits to form a “logical qubit,” and is believed to be the only way to produce a large-scale quantum computer with error rates low enough for useful calculations.
Instead of computing on the individual qubits themselves, we will then compute on logical qubits. By encoding larger numbers of physical qubits on our quantum processor into one logical qubit, we hope to reduce the error rates to enable useful quantum algorithms.

Summary:

"""


SUMMARIZE_PROMPT_3 = """
Provide a TL;DR for the following article:

Our quantum computers work by manipulating qubits in an orchestrated fashion that we call quantum algorithms. 
The challenge is that qubits are so sensitive that even stray light can cause calculation errors — and the problem worsens as quantum computers grow. 
This has significant consequences, since the best quantum algorithms that we know for running useful applications require the error rates of our qubits to be far lower than we have today. 
To bridge this gap, we will need quantum error correction. 
Quantum error correction protects information by encoding it across multiple physical qubits to form a “logical qubit,” and is believed to be the only way to produce a large-scale quantum computer with error rates low enough for useful calculations. 
Instead of computing on the individual qubits themselves, we will then compute on logical qubits. By encoding larger numbers of physical qubits on our quantum processor into one logical qubit, we hope to reduce the error rates to enable useful quantum algorithms.

TL;DR:
"""


SUMMARIZE_PROMPT_4 = """
Provide a very short summary in four bullet points for the following article:

Our quantum computers work by manipulating qubits in an orchestrated fashion that we call quantum algorithms.
The challenge is that qubits are so sensitive that even stray light can cause calculation errors — and the problem worsens as quantum computers grow.
This has significant consequences, since the best quantum algorithms that we know for running useful applications require the error rates of our qubits to be far lower than we have today.
To bridge this gap, we will need quantum error correction.
Quantum error correction protects information by encoding it across multiple physical qubits to form a “logical qubit,” and is believed to be the only way to produce a large-scale quantum computer with error rates low enough for useful calculations.
Instead of computing on the individual qubits themselves, we will then compute on logical qubits. By encoding larger numbers of physical qubits on our quantum processor into one logical qubit, we hope to reduce the error rates to enable useful quantum algorithms.

Bulletpoints:

"""


SUMMARIZE_PROMPT_5 = """
Please generate a summary of the following conversation and at the end summarize the to-do's for the support Agent:

Customer: Hi, I'm Larry, and I received the wrong item.

Support Agent: Hi, Larry. How would you like to see this resolved?

Customer: That's alright. I want to return the item and get a refund, please.

Support Agent: Of course. I can process the refund for you now. Can I have your order number, please?

Customer: It's [ORDER NUMBER].

Support Agent: Thank you. I've processed the refund, and you will receive your money back within 14 days.

Customer: Thank you very much.

Support Agent: You're welcome, Larry. Have a good day!

Summary:
"""

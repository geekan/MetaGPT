#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/19 23:07
@Author  : alexanderwu
@File    : summarize.py
"""

# From the plugin: ChatGPT - Summarize Websites and YouTube Videos
# https://chrome.google.com/webstore/detail/chatgpt-%C2%BB-summarize-every/cbgecfllfhmmnknmamkejadjmnmpfjmp?hl=zh-CN&utm_source=chrome-ntp-launcher
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

# From GCP-VertexAI-Text Summarization
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/prompt-design/text_summarization.ipynb
# For longer documents, a map-reduce process is needed, see the following notebook
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/document-summarization/summarization_large_documents.ipynb
SUMMARIZE_PROMPT_2 = """
Provide a very short summary, no more than three sentences, for the following article:

Our quantum computers work by manipulating qubits in a manner we call quantum algorithms.
The challenge is that qubits are extremely sensitive, to the extent that even stray light can introduce calculation errors — a problem that intensifies as quantum computers scale.
This has notable ramifications since the most effective quantum algorithms we know for executing valuable applications necessitate that our qubits' error rates be significantly lower than current levels.
To address this discrepancy, quantum error correction is essential.
Quantum error correction safeguards information by distributing it over several physical qubits, forming a “logical qubit.” This is believed to be the sole method to create a large-scale quantum computer with sufficiently low error rates for practical calculations.
Rather than computing on individual qubits, we will utilize logical qubits. By transforming a greater number of physical qubits on our quantum processor into a single logical qubit, we aim to reduce error rates, enabling viable quantum algorithms.

Summary:

"""

SUMMARIZE_PROMPT_3 = """
Provide a TL;DR for the following article:

Our quantum computers operate by controlling qubits in a method termed quantum algorithms. 
The problem is that qubits are incredibly delicate, so much so that even minimal light interference can introduce computational errors — and this issue becomes more pronounced as quantum computers expand. 
This is consequential because the most potent quantum algorithms we are aware of, for practical applications, demand that our qubits' error rates be substantially below current standards. 
To mitigate this, quantum error correction is pivotal. 
Quantum error correction secures data by distributing it across numerous physical qubits, generating a “logical qubit.” It's believed to be the exclusive approach to develop a large-scale quantum computer with error rates low enough for practical operations. 
Instead of operations on individual qubits, we'll focus on logical qubits. By encoding a greater number of physical qubits on our quantum device into a single logical qubit, we aspire to diminish error rates and enable efficient quantum algorithms.

TL;DR:
"""

SUMMARIZE_PROMPT_4 = """
Provide a very short summary in four bullet points for the following article:

Our quantum computers function by manipulating qubits through a method known as quantum algorithms.
The dilemma is that qubits are exceedingly fragile, so much so that even minimal light can lead to computational inaccuracies — and this problem amplifies as quantum computers become larger.
This is significant because the most proficient quantum algorithms known to us, suitable for real-world applications, necessitate that our qubits' error rates be significantly below what we currently observe.
To bridge this disparity, quantum error correction becomes indispensable.
Quantum error correction secures data by spreading it across multiple physical qubits, resulting in a “logical qubit.” It's perceived as the only technique to manufacture a large-scale quantum computer with error rates sufficiently low for practical tasks.
Instead of operating on individual qubits directly, we'll be utilizing logical qubits. By converting more physical qubits on our quantum machine into a single logical qubit, we intend to lower error rates, facilitating effective quantum algorithms.

Bulletpoints:

"""

SUMMARIZE_PROMPT_5 = """
Please generate a summary of the following conversation and at the end summarize the to-do's for the support Agent:

Customer: Hi, I'm Larry, and I received the wrong item.

Support Agent: Hi, Larry. How would you like this issue to be resolved?

Customer: That's alright. I'd like to return the item and receive a refund, please.

Support Agent: Certainly. I can process the refund for you right now. Could I have your order number, please?

Customer: It's [ORDER NUMBER].

Support Agent: Thanks. I've processed the refund, and you should receive your funds within 14 days.

Customer: I appreciate it.

Support Agent: You're welcome, Larry. Have a great day!

Summary:
"""

# - def summarize(doc: str) -> str # Input a document and receive a summary.

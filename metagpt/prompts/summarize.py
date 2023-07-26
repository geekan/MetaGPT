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
Your output should follow the template below:
### Summary
### Facts
- [Emoji] Bulletpoint

Your task is to summarize the text I provide you with in up to seven concise bullet points, and start with a brief, high-quality summary. Choose a suitable emoji for every bullet point. Your response should be in {{SELECTED_LANGUAGE}}. If a provided URL is functional and not a YouTube video, use the text from the {{URL}}. If the URL is non-functional or is a YouTube video, use the following text: {{CONTENT}}.
"""

# From GCP-VertexAI-Text Summary (SUMMARIZE_PROMPT_2-5 are all from this source)
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/prompt-design/text_summarization.ipynb
# For long documents, a map-reduce process is required. See the notebook below:
# https://github.com/GoogleCloudPlatform/generative-ai/blob/main/language/examples/document-summarization/summarization_large_documents.ipynb
SUMMARIZE_PROMPT_2 = """
Provide a very short summary, no more than three sentences, for the following article:

Quantum computers operate by manipulating qubits through orchestrated patterns called quantum algorithms.
The challenge is that qubits are so delicate that even stray light can introduce computational errors, and this issue escalates as quantum computers expand.
This is consequential since the best quantum algorithms known for practical applications demand much lower qubit error rates than current levels.
To overcome this, quantum error correction is essential.
Quantum error correction shields data by encoding it across various physical qubits, forming a “logical qubit”. This is believed to be the sole method to build a large-scale quantum computer with sufficiently low error rates for beneficial computations.
Rather than computing on individual qubits, we'll compute on these logical qubits. We aim to decrease error rates by encoding a larger set of physical qubits on our quantum processor into one logical qubit.

Summary:

"""

SUMMARIZE_PROMPT_3 = """
Provide a TL;DR for the following article:

Quantum computers operate by manipulating qubits through orchestrated patterns known as quantum algorithms. 
Qubits are so delicate that even stray light can cause computational errors, a problem that escalates with the growth of quantum computers. 
This presents a significant issue because the best quantum algorithms we have for practical applications necessitate much lower qubit error rates than what we currently achieve. 
To address this, quantum error correction is needed. 
Quantum error correction safeguards data by encoding it across multiple physical qubits, creating a “logical qubit”. It's believed to be the only method to develop a large-scale quantum computer with sufficiently low error rates for beneficial computations. 
Instead of performing computations on individual qubits, calculations will be done on these logical qubits. Our goal is to lower error rates by encoding a greater number of physical qubits on our quantum processor into a single logical qubit.

TL;DR:
"""

SUMMARIZE_PROMPT_4 = """
Provide a very short summary in four bullet points for the following article:

Quantum computers operate by controlling qubits in orchestrated patterns termed quantum algorithms.
The issue is that qubits are extremely delicate, so much so that even stray light can lead to computational errors. This problem becomes more severe as quantum computers become larger.
This is a significant hurdle because the most effective quantum algorithms known for real-world applications necessitate qubit error rates much lower than what's currently achieved.
To bridge this gap, we need quantum error correction.
Quantum error correction defends data by encoding it across various physical qubits, resulting in a “logical qubit”. It's considered the only way to craft a large-scale quantum computer with sufficiently low error rates for practical computations.
Instead of computing using individual qubits, we'll use these logical qubits. Our aim is to diminish error rates by encoding many physical qubits on our quantum processor into one logical qubit.

Bulletpoints:

"""

SUMMARIZE_PROMPT_5 = """
Please summarize the following conversation, and at the end, list the to-do's for the support Agent:

Customer: Hi, I'm Larry, and I received the wrong item.

Support Agent: Hi, Larry. How would you like this to be resolved?

Customer: That's alright. I'd like to return the item and get a refund, please.

Support Agent: Of course. I can process the refund for you now. Can I have your order number, please?

Customer: It's [ORDER NUMBER].

Support Agent: Thanks. I've processed the refund, and you'll receive your money back within 14 days.

Customer: Thank you very much.

Support Agent: You're welcome, Larry. Have a great day!

Summary:
"""

# - def summarize(doc: str) -> str # Input a document and receive a summary.

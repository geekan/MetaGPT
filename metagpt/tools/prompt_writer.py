#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 16:03
@Author  : alexanderwu
@File    : prompt_writer.py
"""
from typing import Union


class GPTPromptGenerator:
    """Using LLM, given an output, request LLM to provide input (supporting instruction, chatbot, and query styles)"""

    def __init__(self):
        self._generators = {i: getattr(self, f"gen_{i}_style") for i in ["instruction", "chatbot", "query"]}

    def gen_instruction_style(self, example):
        """Instruction style: Given an output, request LLM to provide input"""
        return f"""Instruction: X
Output: {example}
What kind of instruction might this output come from?
X:"""

    def gen_chatbot_style(self, example):
        """Chatbot style: Given an output, request LLM to provide input"""
        return f"""You are a chatbot. A user sent you an informal message, and you replied as follows.
Message: X
Reply: {example}
What could the informal message X be?
X:"""

    def gen_query_style(self, example):
        """Query style: Given an output, request LLM to provide input"""
        return f"""You are a search engine. Someone made a detailed query, and the most relevant document to this query is as follows.
Query: X
Document: {example} What is the detailed query X?
X:"""

    def gen(self, example: str, style: str = "all") -> Union[list[str], str]:
        """
        Generate one or multiple outputs using the example, allowing LLM to reply with the corresponding input

        :param example: Expected LLM output sample
        :param style: (all|instruction|chatbot|query)
        :return: Expected LLM input sample (one or multiple)
        """
        if style != "all":
            return self._generators[style](example)
        return [f(example) for f in self._generators.values()]


class WikiHowTemplate:
    def __init__(self):
        self._prompts = """Give me {step} steps to {question}.
How to {question}?
Do you know how can I {question}?
List {step} instructions to {question}.
What are some tips to {question}?
What are some steps to {question}?
Can you provide {step} clear and concise instructions on how to {question}?
I'm interested in learning how to {question}. Could you break it down into {step} easy-to-follow steps?
For someone who is new to {question}, what would be {step} key steps to get started?
What is the most efficient way to {question}? Could you provide a list of {step} steps?
Do you have any advice on how to {question} successfully? Maybe a step-by-step guide with {step} steps?
I'm trying to accomplish {question}. Could you walk me through the process with {step} detailed instructions?
What are the essential {step} steps to {question}?
I need to {question}, but I'm not sure where to start. Can you give me {step} actionable steps?
As a beginner in {question}, what are the {step} basic steps I should take?
I'm looking for a comprehensive guide on how to {question}. Can you provide {step} detailed steps?
Could you outline {step} practical steps to achieve {question}?
What are the {step} fundamental steps to consider when attempting to {question}?"""

    def gen(self, question: str, step: str) -> list[str]:
        return self._prompts.format(question=question, step=step).splitlines()


class EnronTemplate:
    def __init__(self):
        self._prompts = """Write an email with the subject "{subj}".
Can you craft an email with the subject {subj}?
Would you be able to compose an email and use {subj} as the subject?
Create an email about {subj}.
Draft an email and include the subject "{subj}".
Generate an email about {subj}.
Hey, can you shoot me an email about {subj}?
Do you mind crafting an email for me with {subj} as the subject?
Can you whip up an email with the subject of "{subj}"?
Hey, can you write an email and use "{subj}" as the subject?
Can you send me an email about {subj}?"""

    def gen(self, subj):
        return self._prompts.format(subj=subj).splitlines()


class BEAGECTemplate:
    def __init__(self):
        self._prompts = """Edit and revise this document to improve its grammar, vocabulary, spelling, and style.
Revise this document to correct all the errors related to grammar, spelling, and style.
Refine this document by eliminating all grammatical, lexical, and orthographic errors and improving its writing style.
Polish this document by rectifying all errors related to grammar, vocabulary, and writing style.
Enhance this document by correcting all the grammar errors and style issues, and improving its overall quality.
Rewrite this document by fixing all grammatical, lexical and orthographic errors.
Fix all grammar errors and style issues and rewrite this document.
Take a stab at fixing all the mistakes in this document and make it sound better.
Give this document a once-over and clean up any grammar or spelling errors.
Tweak this document to make it read smoother and fix any mistakes you see.
Make this document sound better by fixing all the grammar, spelling, and style issues.
Proofread this document and fix any errors that make it sound weird or confusing."""

    def gen(self):
        return self._prompts.splitlines()

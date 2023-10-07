#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18 09:51
@Author  : stellahong
@File    : __init__.py
"""

MODEL_SELECTION_PROMPT = """Please help me find a suitable model for painting in this scene.
Model list will be given in the format like:
'''
model_name: model desc,
'''

you should select the model and tell me the model name. answer it in the form like Model: model_name || Domain:xxx

###
Model List:
{model_info}

My scene is: {query}
"""

DOMAIN_JUDGEMENT_TEMPLATE = '''
use model {model_name}, decide the domain, answer it in the form like Domain: xxx

###
Model Information:
{model_info}

'''

MODEL_SELECTION_OUTPUT_MAPPING = {
    "Model:": (str, ...), }

SD_PROMPT_KW_OPTIMIZE_TEMPLATE = '''
I want you to act as a prompt generator. Compose each answer as a visual sentence. Do not write explanations on replies. Format the answers as javascript json arrays with a single string per answer. Return exactly {answer_count} to my question. Answer the questions exactly, in the form like responses:xxx. Answer the following question:

Find 3 keywords related to the prompt "{messages}" that are not found in the prompt. The keywords should be related to each other. Each keyword is a single word.

'''

SD_PROMPT_IMPROVE_OPTIMIZE_TEMPLATE = '''
I want you to act as a prompt generator. Compose each answer as a visual sentence. Do not write explanations on replies. Format the answers as javascript json arrays with a single string per answer. Return exactly {answer_count} to my question. Answer the questions exactly, in the form like responses:xxx. Answer the following question:

domain is {domain}

if domain is anime or game like,  Take the prompt "{messages}, Cute kawaii sticker , white background,  vector, pastel colors" and improve it.

if domain is realistic like, Take the prompt "{messages}" and improve it.

'''
# Die-cut sticker, illustration minimalism,

FORMAT_INSTRUCTIONS = """The problem is to make the user input a better text2image prompt, the input is {query}"

    Let's first understand the problem and devise a plan to solve the problem.

    Based on the text2image model selected {model_name} and domain {domain}
    You have access to the following tools:

    {tool_names}
    {tool_description}

    Use a json blob to specify a tool by providing an action key (tool name) and an Observation (tool description).

    Valid "action" values: {tool_names}

    Provide only ONE action per $JSON_BLOB, as shown:

    ```
    {{{{
      "action": $TOOL_NAME,
      "Observation": $TOOL_DESCRIPTION
    }}}}
    ```

    Follow this format:

    ## Think Chain
    ```
    Question: input question to answer
    Thought: select a better method for the input by go through these two tools and its observations respectively
    Action1:
    ```
    $JSON_BLOB
    ```
    Action2:
    ```
    $JSON_BLOB
    ```

    Thought:When evaluating a prompt's richness, I need to specify which tool to use and I can only select one tool . To finish this selection, in the form:
    ## Final Action:
    TOOL_NAME
    
    """

PROMPT_OUTPUT_MAPPING = {
    "Final Action:": (str, ...),
}

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the prompt templates of phone operation

tap_doc_template = """I will give you the screenshot of a mobile app before and after tapping the UI element labeled 
with the number {ui_element} on the screen. The numeric tag of each element is located at the center of the element. 
Tapping this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. Your task is to 
describe the functionality of the UI element concisely in one or two sentences. Notice that your description of the UI 
element should focus on the general function. For example, if the UI element is used to navigate to the chat window 
with John, your description should not include the name of the specific person. Just say: "Tapping this area will 
navigate the user to the chat window". Never include the numeric tag of the UI element in your description. You can use 
pronouns such as "the UI element" to refer to the element."""

text_doc_template = """I will give you the screenshot of a mobile app before and after typing in the input area labeled
with the number {ui_element} on the screen. The numeric tag of each element is located at the center of the element. 
Typing in this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. Your task is 
to describe the functionality of the UI element concisely in one or two sentences. Notice that your description of the 
UI element should focus on the general function. For example, if the change of the screenshot shows that the user typed 
"How are you?" in the chat box, you do not need to mention the actual text. Just say: "This input area is used for the 
user to type a message to send to the chat window.". Never include the numeric tag of the UI element in your 
description. You can use pronouns such as "the UI element" to refer to the element."""

long_press_doc_template = """I will give you the screenshot of a mobile app before and after long pressing the UI 
element labeled with the number {ui_element} on the screen. The numeric tag of each element is located at the center of 
the element. Long pressing this UI element is a necessary part of proceeding with a larger task, which is to 
<task_desc>. Your task is to describe the functionality of the UI element concisely in one or two sentences. Notice 
that your description of the UI element should focus on the general function. For example, if long pressing the UI 
element redirects the user to the chat window with John, your description should not include the name of the specific 
person. Just say: "Long pressing this area will redirect the user to the chat window". Never include the numeric tag of 
the UI element in your description. You can use pronouns such as "the UI element" to refer to the element."""

swipe_doc_template = """I will give you the screenshot of a mobile app before and after swiping <swipe_dir> the UI 
element labeled with the number {ui_element} on the screen. The numeric tag of each element is located at the center of 
the element. Swiping this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. 
Your task is to describe the functionality of the UI element concisely in one or two sentences. Notice that your 
description of the UI element should be as general as possible. For example, if swiping the UI element increases the 
contrast ratio of an image of a building, your description should be just like this: "Swiping this area enables the 
user to tune a specific parameter of the image". Never include the numeric tag of the UI element in your description. 
You can use pronouns such as "the UI element" to refer to the element."""

refine_doc_suffix = """\nA documentation of this UI element generated from previous demos is shown below. Your 
generated description should be based on this previous doc and optimize it. Notice that it is possible that your 
understanding of the function of the UI element derived from the given screenshots conflicts with the previous doc, 
because the function of a UI element can be flexible. In this case, your generated description should combine both.
Old documentation of this UI element: {old_doc}"""

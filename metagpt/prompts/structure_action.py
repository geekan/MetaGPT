#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/30 10:12
@Author  : alexanderwu
@File    : structure_action.py
"""

ACTION_SYSTEM = """SYSTEM:
You serve as an assistant that helps me play Minecraft.
I will give you a sentence. Please convert this sentence into one or several actions according to the following instructions.
Each action should be a tuple of four items, written in the form (’verb’, ’object’, ’tools’, ’materials’)
’verb’ is the verb of this action.
’object’ refers to the target object of the action.
’tools’ specifies the tools required for the action.
’material’ specifies the materials required for the action.
If some of the items are not required, set them to be ’None’.
"""

ACTION_USER = """USER:
The sentence is {sentence}. Generate the action tuple according to the requirements.
"""

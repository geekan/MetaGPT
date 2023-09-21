#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/20 12:15
@Author  : mczhuge
@File    : reflect.py
"""

import json
from metagpt.actions import Action
from metagpt.provider import OpenAIGPTAPI
from metagpt.config import CONFIG

FEEDBACK_EXAMPLE = """
When you work on the "{proj_name}" project, others provide the following suggestion: {handover_feedback}
"""

PROMPT_TEMPLATE = """
You work as a {role} at a software company.

You've previously followed certain constraints:

### Constraints
{constraints}

After collaborating with your colleagues, they've provided you with important feedback:

### Feedback
{whole_feedback}

You can choose to accept suggestions that align with your role. Don't forget the original constraints.

Now, rewrite your "{role}" constraints in 30 words:
"""

# def print_with_color(text, color="red"):

#     color_codes = {
#         'reset': '\033[0m',
#         'red': '\033[91m',
#         'green': '\033[92m',
#         'yellow': '\033[93m',
#         'blue': '\033[94m',
#     }
#     print(f"{color_codes[color]}  {text} {color_codes['reset']}")

class Reflect():
    def from_feedback(role, constraints):

        chat = OpenAIGPTAPI()
        with open(CONFIG.handover_file, "r") as file:
            data = json.load(file)

        feedback_for_role = []
        for key, feedback_data in data.items():
            if 'Project Name' in feedback_data:
                feedback_for_role.append(FEEDBACK_EXAMPLE.format(proj_name=feedback_data['Project Name'],
                                                                 handover_feedback=feedback_data[role.replace(" ", "")]))

        whole_feedback = "\n".join(feedback_for_role)
        new_constraints = chat.ask(msg = PROMPT_TEMPLATE.format(role=role,
                                                         constraints=constraints,
                                                         whole_feedback=whole_feedback))
        
        return new_constraints

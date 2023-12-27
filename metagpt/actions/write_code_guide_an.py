#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mannaandpoem
@File    : write_code_guide_an.py
"""
import asyncio

from pydantic import Field

from metagpt.actions.action import Action
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.schema import Document

GUIDELINE = ActionNode(
    key="Code Guideline",
    expected_type=list[str],
    instruction="You are a professional software engineer, and your main task is to "
    "proposing incremental development plans and code guidance",
    example=[
        "`calculator.py` should be extended to include methods for subtraction, multiplication, and division. Error handling should be implemented for division to prevent division by zero.",
        "New endpoints for subtraction, multiplication, and division should be added to `main.py`.",
    ],
)

INCREMENTAL_CHANGE = ActionNode(
    key="Incremental Change",
    expected_type=str,
    instruction="Write Incremental Change by making a code draft that how to implement incremental development based on the context and Code Guideline.",
    example="""1. Extend `Calculator` class in `calculator.py` with new methods for subtraction, multiplication, and division.
```python
## calculator.py
class Calculator:
    ...
    def subtract_numbers(self, num1: int, num2: int) -> int:
        return num1 - num2
    def multiply_numbers(self, num1: int, num2: int) -> int:
        return num1 * num2
    def divide_numbers(self, num1: int, num2: int) -> float:
        if num2 == 0:
            raise ValueError('Cannot divide by zero')
        return num1 / num2
```
2. Implement new endpoints in `main.py` for the subtraction, multiplication, and division methods.
```python
## main.py
from flask import Flask, request, jsonify
from calculator import Calculator
app = Flask(__name__)
calculator = Calculator()
...
@app.route('/subtract_numbers', methods=['POST'])
def subtract_numbers():
    data = request.get_json()
    num1 = data.get('num1', 0)
    num2 = data.get('num2', 0)
    result = calculator.subtract_numbers(num1, num2)
    return jsonify({'result': result}), 200
@app.route('/multiply_numbers', methods=['POST'])
def multiply_numbers():
    data = request.get_json()
    num1 = data.get('num1', 0)
    num2 = data.get('num2', 0)
    result = calculator.multiply_numbers(num1, num2)
    return jsonify({'result': result}), 200
@app.route('/divide_numbers', methods=['POST'])
def divide_numbers():
    data = request.get_json()
    num1 = data.get('num1', 1)
    num2 = data.get('num2', 1)
    try:
        result = calculator.divide_numbers(num1, num2)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'result': result}), 200
if __name__ == '__main__':
    app.run()
```""",
)

CODE_GUIDE_CONTEXT = """
### NOTICE
Role: You are a professional software engineer, and your main task is to write code Guideline and code craft with triple quote, based on the following attentions and context. Output format carefully referenced "Format example".
1. Determine the scope of responsibilities of each file and what classes and methods need to be implemented.
2. Import all referenced classes.
3. Implement all methods. 
4. Add necessary explanation to all methods. 
5. Ensure there are no potential bugs.
6. Confirm that the entire project conforms to the tasks proposed by the user.
7. Examine the code closely to find and fix errors, and confirm that the logic is sound to ensure smooth user interaction while meeting all specified requirements.
8. Attention: Code files in the task list may have a different number of files compared to legacy code files. This requires integrating legacy code files that do not appear in the task list into the code files of the task list. Therefore, when writing code guidance and incremental changes for the code files in the task list, also include how to seamlessly merge and adjust legacy code files.

### Requirement
{requirement}

### Prd
{prd}

### Design
{design}

### Tasks
{tasks}

### Legacy Code
{code}
"""

WRITE_CODE_INCREMENT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; The main goal is to complete incremental development by combining Legacy Code and Guideline to rewrite the complete code.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
## Guideline
{guideline}

## Design
{design}

## Tasks
{tasks}

## Legacy Code
```Code
{code}
```

## Debug logs
```text
{logs}

{summary_log}
```

## Bug Feedback logs
```text
{feedback}
```

# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context, follow "Format example", write code.

## Rewrite Complete Code: Only Write one file {filename}, Write code using triple quotes, based on the following attentions and context.
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
4. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
5. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
6. Before using a external variable/module, make sure you import it first.
7. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.
8. When Task List code files do not include Legacy Code files, you need to seamlessly merge and adjust Legacy Code files that do not appear in the Task List into the code files of the task list being written based on the guideline.
9. Attention: Make modifications and additions to the legacy code in accordance with the provided guidelines and API. Ensure that the complete code is implemented without any omissions. 
"""

CODE_GUIDE_CONTEXT_EXAMPLE = """
### Legacy Code
## main.py

from flask import Flask, request, jsonify
from calculator import Calculator

app = Flask(__name__)
calculator = Calculator()

@app.route('/add_numbers', methods=['POST'])
def add_numbers():
    data = request.get_json()
    num1 = data.get('num1', 0)
    num2 = data.get('num2', 0)
    result = calculator.add_numbers(num1, num2)
    return jsonify({'result': result}), 200

if __name__ == '__main__':
    app.run()

## calculator.py

class Calculator:
    def __init__(self, num1: int = 0, num2: int = 0):
        self.num1 = num1
        self.num2 = num2

    def add_numbers(self, num1: int, num2: int) -> int:
        return num1 + num2
"""

GUIDE_NODES = [GUIDELINE, INCREMENTAL_CHANGE]

WRITE_CODE_GUIDE_NODE = ActionNode.from_children("WriteCodeGuide", GUIDE_NODES)


class WriteCodeGuide(Action):
    name: str = "WriteCodeGuide"
    context: Document = Field(default_factory=Document)
    llm: BaseGPTAPI = Field(default_factory=LLM)

    async def run(self, context):
        return await WRITE_CODE_GUIDE_NODE.fill(context=context, llm=self.llm, schema="json")


def main():
    action = WriteCodeGuide()
    return asyncio.run(action.run(CODE_GUIDE_CONTEXT))


if __name__ == "__main__":
    main()

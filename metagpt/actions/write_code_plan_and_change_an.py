#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mannaandpoem
@File    : write_code_plan_and_change_an.py
"""
import os
from typing import List

from pydantic import Field

from metagpt.actions.action import Action
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.schema import CodePlanAndChangeContext

DEVELOPMENT_PLAN = ActionNode(
    key="Development Plan",
    expected_type=List[str],
    instruction="Develop a comprehensive and step-by-step incremental development plan, providing the detail "
    "changes to be implemented at each step based on the order of 'Task List'",
    example=[
        "Enhance the functionality of `calculator.py` by extending it to incorporate methods for subtraction, ...",
        "Update the existing codebase in main.py to incorporate new API endpoints for subtraction, ...",
    ],
)

INCREMENTAL_CHANGE = ActionNode(
    key="Incremental Change",
    expected_type=List[str],
    instruction="Write Incremental Change by making a code draft that how to implement incremental development "
    "including detailed steps based on the context. Note: Track incremental changes using the marks `+` and `-` to "
    "indicate additions and deletions, and ensure compliance with the output format of `git diff`",
    example=[
        '''```diff
--- Old/calculator.py
+++ New/calculator.py

class Calculator:
         self.result = number1 + number2
         return self.result

-    def sub(self, number1, number2) -> float:
+    def subtract(self, number1: float, number2: float) -> float:
+        """
+        Subtracts the second number from the first and returns the result.
+
+        Args:
+            number1 (float): The number to be subtracted from.
+            number2 (float): The number to subtract.
+
+        Returns:
+            float: The difference of number1 and number2.
+        """
+        self.result = number1 - number2
+        return self.result
+
    def multiply(self, number1: float, number2: float) -> float:
-        pass
+        """
+        Multiplies two numbers and returns the result.
+
+        Args:
+            number1 (float): The first number to multiply.
+            number2 (float): The second number to multiply.
+
+        Returns:
+            float: The product of number1 and number2.
+        """
+        self.result = number1 * number2
+        return self.result
+
    def divide(self, number1: float, number2: float) -> float:
-        pass
+        """
+            ValueError: If the second number is zero.
+        """
+        if number2 == 0:
+            raise ValueError('Cannot divide by zero')
+        self.result = number1 / number2
+        return self.result
+
-    def reset_result(self):
+    def clear(self):
+        if self.result != 0.0:
+            print("Result is not zero, clearing...")
+        else:
+            print("Result is already zero, no need to clear.")
+
         self.result = 0.0
```''',
        """```diff
--- Old/main.py
+++ New/main.py

def add_numbers():
     result = calculator.add_numbers(num1, num2)
     return jsonify({'result': result}), 200

-# TODO: Implement subtraction, multiplication, and division operations
+@app.route('/subtract_numbers', methods=['POST'])
+def subtract_numbers():
+    data = request.get_json()
+    num1 = data.get('num1', 0)
+    num2 = data.get('num2', 0)
+    result = calculator.subtract_numbers(num1, num2)
+    return jsonify({'result': result}), 200
+
+@app.route('/multiply_numbers', methods=['POST'])
+def multiply_numbers():
+    data = request.get_json()
+    num1 = data.get('num1', 0)
+    num2 = data.get('num2', 0)
+    try:
+        result = calculator.divide_numbers(num1, num2)
+    except ValueError as e:
+        return jsonify({'error': str(e)}), 400
+    return jsonify({'result': result}), 200
+
 if __name__ == '__main__':
     app.run()
```""",
    ],
)

CODE_PLAN_AND_CHANGE_CONTEXT = """
## User New Requirements
{requirement}

## Issue
{issue}

## PRD
{prd}

## Design
{design}

## Task
{task}

## Legacy Code
{code}
"""

REFINED_TEMPLATE = """
NOTICE
Role: You are a professional engineer; The main goal is to complete incremental development by combining legacy code and plan and Incremental Change, ensuring the integration of new features.

# Context
## User New Requirements
{user_requirement}

## Code Plan And Change
{code_plan_and_change}

## Design
{design}

## Task
{task}

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

# Instruction: Based on the context, follow "Format example", write or rewrite code.
## Write/Rewrite Code: Only write one file {filename}, write or rewrite complete code using triple quotes based on the following attentions and context.
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
4. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
5. Follow Code Plan And Change: If there is any "Incremental Change" that is marked by the git diff format with '+' and '-' symbols, or Legacy Code files contain "{filename} to be rewritten", you must merge it into the code file according to the "Development Plan". 
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Before using a external variable/module, make sure you import it first.
8. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.
9. Attention: Retain details that are not related to incremental development but are important for maintaining the consistency and clarity of the old code.
"""

CODE_PLAN_AND_CHANGE = [DEVELOPMENT_PLAN, INCREMENTAL_CHANGE]

WRITE_CODE_PLAN_AND_CHANGE_NODE = ActionNode.from_children("WriteCodePlanAndChange", CODE_PLAN_AND_CHANGE)


class WriteCodePlanAndChange(Action):
    name: str = "WriteCodePlanAndChange"
    i_context: CodePlanAndChangeContext = Field(default_factory=CodePlanAndChangeContext)

    async def run(self, *args, **kwargs):
        self.llm.system_prompt = "You are a professional software engineer, your primary responsibility is to "
        "meticulously craft comprehensive incremental development plan and deliver detailed incremental change"
        prd_doc = await self.repo.docs.prd.get(filename=self.i_context.prd_filename)
        design_doc = await self.repo.docs.system_design.get(filename=self.i_context.design_filename)
        task_doc = await self.repo.docs.task.get(filename=self.i_context.task_filename)
        context = CODE_PLAN_AND_CHANGE_CONTEXT.format(
            requirement=f"```text\n{self.i_context.requirement}\n```",
            issue=f"```text\n{self.i_context.issue}\n```",
            prd=prd_doc.content,
            design=design_doc.content,
            task=task_doc.content,
            code=await self.get_old_codes(),
        )
        logger.info("Writing code plan and change..")
        return await WRITE_CODE_PLAN_AND_CHANGE_NODE.fill(context=context, llm=self.llm, schema="json")

    async def get_old_codes(self) -> str:
        self.repo.old_workspace = self.repo.git_repo.workdir / os.path.basename(self.config.project_path)
        old_file_repo = self.repo.git_repo.new_file_repository(relative_path=self.repo.old_workspace)
        old_codes = await old_file_repo.get_all()
        codes = [f"----- {code.filename}\n```{code.content}```" for code in old_codes]
        return "\n".join(codes)

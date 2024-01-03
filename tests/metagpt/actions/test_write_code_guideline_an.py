#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_code_guideline_an.py
"""
import pytest

from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_guideline_an import (
    CODE_GUIDELINE_CONTEXT,
    CODE_GUIDELINE_SCRIPT_EXAMPLE,
    REFINE_CODE_SCRIPT_EXAMPLE,
    REFINED_CODE_TEMPLATE,
    WriteCodeGuideline,
)

REQUIREMENT_EXAMPLE = """Add subtraction, multiplication and division operations to the calculator.
The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator
"""

DESIGN_EXAMPLE = """
{
  "Refined Implementation Approach": "To accommodate the new requirements, we will extend the existing Python-based calculator application. We will enhance the Tkinter-based UI to include buttons for subtraction, multiplication, and division, alongside the existing addition functionality. We will also implement input validation to handle edge cases such as division by zero. The architecture will be modular, with separate components for the UI, calculation logic, and error handling to maintain simplicity and facilitate future enhancements such as a history feature.",
  "File list": [
    "main.py",
    "calculator.py",
    "interface.py",
    "operations.py"
  ],
  "Refined Data Structures and Interfaces": "classDiagram\n    class CalculatorApp {\n        +main() None\n    }\n    class Calculator {\n        -result float\n        +add(number1: float, number2: float) float\n        +subtract(number1: float, number2: float) float\n        +multiply(number1: float, number2: float) float\n        +divide(number1: float, number2: float) float\n        +clear() None\n    }\n    class Interface {\n        -calculator Calculator\n        +start() None\n        +display_result(result: float) None\n        +get_input() float\n        +show_error(message: str) None\n        +update_operation(operation: str) None\n    }\n    class Operations {\n        +perform_operation(operation: str, number1: float, number2: float) float\n    }\n    CalculatorApp --> Interface\n    Interface --> Calculator\n    Calculator --> Operations",
  "Refined Program call flow": "sequenceDiagram\n    participant CA as CalculatorApp\n    participant I as Interface\n    participant C as Calculator\n    participant O as Operations\n    CA->>I: start()\n    I->>I: get_input()\n    I->>I: update_operation(operation)\n    loop For Each Operation\n        I->>C: perform_operation(operation, number1, number2)\n        C->>O: perform_operation(operation, number1, number2)\n        O-->>C: return result\n        C-->>I: return result\n        I->>I: display_result(result)\n    end\n    I->>I: show_error(message)",
  "Anything UNCLEAR": "The requirement for a history feature is mentioned but not prioritized. It is unclear whether this should be implemented now or in the future. Additionally, there is no specification on the limit to the size of the numbers or the number of operations that can be performed in sequence. These aspects will need clarification for complete implementation."
}
"""

TASKS_EXAMPLE = """
{
  "Required Python packages": [
    "tkinter"
  ],
  "Required Other language third-party packages": [
    "No third-party dependencies required"
  ],
  "Refined Logic Analysis": [
    [
      "main.py",
      "Entry point of the application, creates an instance of the Interface class and starts the application."
    ],
    [
      "calculator.py",
      "Contains the Calculator class with add, subtract, multiply, divide and clear methods for performing arithmetic operations."
    ],
    [
      "interface.py",
      "Contains the Interface class responsible for the GUI, interacts with Calculator for the logic and displays results or errors."
    ],
    [
      "operations.py",
      "Contains the Operations class with perform_operation method that delegates the arithmetic operation based on the operation argument."
    ]
  ],
  "Refined Task list": [
    "operations.py",
    "calculator.py",
    "interface.py",
    "main.py"
  ],
  "Full API spec": "",
  "Refined Shared Knowledge": "`interface.py` will use the Calculator class from `calculator.py` to perform operations and display results. `main.py` will be the starting point that initializes the Interface. `calculator.py` will now also interact with `operations.py` to perform the arithmetic operations.",
  "Anything UNCLEAR": "The requirement for a history feature is mentioned but not prioritized. It is unclear whether this should be implemented now or in the future. Additionally, there is no specification on the limit to the size of the numbers or the number of operations that can be performed in sequence. These aspects will need clarification for complete implementation."
}
"""

INCREMENTAL_CHANGE_EXAMPLE = """
{
    "Incremental Change": "- operations.py: Implement the Operations class with a method to perform the requested arithmetic operation. This class will be used by the Calculator class to execute the operations.\n```python\n## operations.py\nclass Operations:\n    @staticmethod\n    def perform_operation(operation: str, number1: float, number2: float) -> float:\n        if operation == 'add':\n            return number1 + number2\n        elif operation == 'subtract':\n            return number1 - number2\n        elif operation == 'multiply':\n            return number1 * number2\n        elif operation == 'divide':\n            if number2 == 0:\n                raise ValueError('Cannot divide by zero')\n            return number1 / number2\n        else:\n            raise ValueError('Invalid operation')\n```\n\n- calculator.py: Extend the Calculator class to include methods for subtraction, multiplication, and division. These methods will utilize the Operations class to perform the actual calculations.\n```python\n## calculator.py\nfrom operations import Operations\nclass Calculator:\n    ...\n    def subtract(self, number1: float, number2: float) -> float:\n        return Operations.perform_operation('subtract', number1, number2)\n\n    def multiply(self, number1: float, number2: float) -> float:\n        return Operations.perform_operation('multiply', number1, number2)\n\n    def divide(self, number1: float, number2: float) -> float:\n        return Operations.perform_operation('divide', number1, number2)\n```\n\n- interface.py: Update the Interface class to include buttons for subtraction, multiplication, and division, and link them to the corresponding methods in the Calculator class. Also, handle the display of errors such as division by zero.\n```python\n## interface.py\nimport tkinter as tk\nfrom tkinter import messagebox\nfrom calculator import Calculator\n...\nclass Interface:\n    ...\n    def create_widgets(self):\n        ...\n        self.subtract_button = tk.Button(self.root, text='-', command=self.subtract, font=('Arial', 18))\n        self.subtract_button.grid(row=3, column=0, sticky='nsew')\n\n        self.multiply_button = tk.Button(self.root, text='*', command=self.multiply, font=('Arial', 18))\n        self.multiply_button.grid(row=3, column=1, sticky='nsew')\n\n        self.divide_button = tk.Button(self.root, text='/', command=self.divide, font=('Arial', 18))\n        self.divide_button.grid(row=3, column=2, sticky='nsew')\n        ...\n\n    def subtract(self):\n        number1, number2 = self.get_input()\n        if number1 is not None and number2 is not None:\n            result = self.calculator.subtract(number1, number2)\n            self.display_result(result)\n\n    def multiply(self):\n        number1, number2 = self.get_input()\n        if number1 is not None and number2 is not None:\n            result = self.calculator.multiply(number1, number2)\n            self.display_result(result)\n\n    def divide(self):\n        number1, number2 = self.get_input()\n        if number1 is not None and number2 is not None:\n            try:\n                result = self.calculator.divide(number1, number2)\n            except ValueError as e:\n                self.show_error(str(e))\n                return\n            self.display_result(result)\n```\n\n- main.py: No changes needed in main.py as it serves as the entry point and will run the updated Interface class.\n```python\n## main.py\nfrom interface import Interface\n...\n```\n\nNote: Ensure that the new operations buttons in the Interface class are properly arranged and that the grid layout is adjusted accordingly. Also, make sure to import the messagebox module from tkinter for error handling."
}
"""


@pytest.mark.asyncio
async def test_write_code_guideline_an():
    write_code_guideline = WriteCodeGuideline()
    context = CODE_GUIDELINE_CONTEXT.format(
        requirement=REQUIREMENT_EXAMPLE, design=DESIGN_EXAMPLE, tasks=TASKS_EXAMPLE, code=CODE_GUIDELINE_SCRIPT_EXAMPLE
    )
    node = await write_code_guideline.run(context=context)
    assert node.instruct_content
    assert "Incremental Change" in node.instruct_content.json(ensure_ascii=False)


@pytest.mark.asyncio
async def test_refine_code():
    prompt = REFINED_CODE_TEMPLATE.format(
        requirement=REQUIREMENT_EXAMPLE,
        guideline=INCREMENTAL_CHANGE_EXAMPLE,
        design=DESIGN_EXAMPLE,
        tasks=TASKS_EXAMPLE,
        code=REFINE_CODE_SCRIPT_EXAMPLE,
        logs="",
        feedback="",
        filename="interface.py",
        summary_log="",
    )
    code = await WriteCode().write_code(prompt=prompt)
    assert code
    assert "def create_widgets" in code

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mannaandpoem
@File    : write_code_guideline_an.py
"""
import asyncio

from metagpt.actions.action import Action
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger

GUIDELINES_AND_INCREMENTAL_CHANGE = ActionNode(
    key="Guidelines and Incremental Change",
    expected_type=str,
    instruction="Developing comprehensive and step-by-step incremental development guideline, and Write Incremental "
    "Change by making a code draft that how to implement incremental development including detailed steps based on the "
    "context. Note: Track incremental changes using mark of '+' or '-' for add/modify/delete code, and conforms to the "
    "output format of git diff",
    example="""
1. Guideline for calculator.py: Enhance the functionality of `calculator.py` by extending it to incorporate methods for subtraction, multiplication, and division. Additionally, implement robust error handling for the division operation to mitigate potential issues related to division by zero. 
```python
class Calculator:
         self.result = number1 + number2
         return self.result

-    def sub(self, number1, number2) -> float:
+    def subtract(self, number1: float, number2: float) -> float:
+        '''
+        Subtracts the second number from the first and returns the result.
+
+        Args:
+            number1 (float): The number to be subtracted from.
+            number2 (float): The number to subtract.
+
+        Returns:
+            float: The difference of number1 and number2.
+        '''
+        self.result = number1 - number2
+        return self.result
+
    def multiply(self, number1: float, number2: float) -> float:
-        pass
+        '''
+        Multiplies two numbers and returns the result.
+
+        Args:
+            number1 (float): The first number to multiply.
+            number2 (float): The second number to multiply.
+
+        Returns:
+            float: The product of number1 and number2.
+        '''
+        self.result = number1 * number2
+        return self.result
+
    def divide(self, number1: float, number2: float) -> float:
-        pass
+        '''
+            ValueError: If the second number is zero.
+        '''
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
```

2. Guideline for main.py: Integrate new API endpoints for subtraction, multiplication, and division into the existing codebase of `main.py`. Then, ensure seamless integration with the overall application architecture and maintain consistency with coding standards.
```python
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
)

CODE_GUIDELINE_CONTEXT = """
## User New Requirements
{user_requirement}

## Product Requirement Pool
{product_requirement_pools}

## Design
{design}

## Tasks
{tasks}

## Legacy Code
{code}
"""

CODE_GUIDELINE_CONTEXT_EXAMPLE = """
## New Requirements
Add subtraction, multiplication and division operations to the calculator.
The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator

## Design
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

## Tasks
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

## Legacy Code
----- calculator.py
```## calculator.py

class Calculator:
    def __init__(self):
        self.result = 0.0  # Default value for the result

    def add(self, number1: float, number2: float) -> float:
        '''
        Adds two numbers and returns the result.

        Args:
            number1 (float): The first number to add.
            number2 (float): The second number to add.

        Returns:
            float: The sum of number1 and number2.
        '''
        self.result = number1 + number2
        return self.result

    def clear(self) -> None:
        '''
        Clears the result to its default value.
        '''
        self.result = 0.0
```

---- interface.py
```## interface.py
import tkinter as tk
from calculator import Calculator

class Interface:
    def __init__(self):
        self.calculator = Calculator()
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.create_widgets()

    def create_widgets(self):
        self.result_var = tk.StringVar()
        self.result_display = tk.Entry(self.root, textvariable=self.result_var, state='readonly', justify='right', font=('Arial', 24))
        self.result_display.grid(row=0, column=0, columnspan=4, sticky='nsew')

        self.entry_number1 = tk.Entry(self.root, justify='right', font=('Arial', 18))
        self.entry_number1.grid(row=1, column=0, columnspan=2, sticky='nsew')

        self.entry_number2 = tk.Entry(self.root, justify='right', font=('Arial', 18))
        self.entry_number2.grid(row=1, column=2, columnspan=2, sticky='nsew')

        self.add_button = tk.Button(self.root, text='+', command=self.add, font=('Arial', 18))
        self.add_button.grid(row=2, column=0, sticky='nsew')

        self.clear_button = tk.Button(self.root, text='C', command=self.clear, font=('Arial', 18))
        self.clear_button.grid(row=2, column=1, sticky='nsew')

        self.quit_button = tk.Button(self.root, text='Quit', command=self.root.quit, font=('Arial', 18))
        self.quit_button.grid(row=2, column=2, columnspan=2, sticky='nsew')

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def start(self):
        self.root.mainloop()

    def display_result(self, result: float):
        self.result_var.set(str(result))

    def get_input(self):
        try:
            number1 = float(self.entry_number1.get())
            number2 = float(self.entry_number2.get())
            return number1, number2
        except ValueError:
            self.show_error("Invalid input! Please enter valid numbers.")
            return None, None

    def add(self):
        number1, number2 = self.get_input()
        if number1 is not None and number2 is not None:
            result = self.calculator.add(number1, number2)
            self.display_result(result)

    def clear(self):
        self.entry_number1.delete(0, tk.END)
        self.entry_number2.delete(0, tk.END)
        self.result_var.set("")

    def show_error(self, message: str):
        tk.messagebox.showerror("Error", message)

# This code is meant to be used as a module and not as a standalone script.
# The Interface class will be instantiated and started by the main.py file.
```

---- main.py
```## main.py
from interface import Interface


class CalculatorApp:
    @staticmethod
    def main():
        interface = Interface()
        interface.start()


if __name__ == "__main__":
    CalculatorApp.main()
```
"""

REFINE_CODE_SCRIPT_EXAMPLE = """
----- calculator.py
```## calculator.py

class Calculator:
    def __init__(self):
        self.result = 0.0  # Default value for the result

    def add(self, number1: float, number2: float) -> float:
        '''
        Adds two numbers and returns the result.

        Args:
            number1 (float): The first number to add.
            number2 (float): The second number to add.

        Returns:
            float: The sum of number1 and number2.
        '''
        self.result = number1 + number2
        return self.result

    def clear(self) -> None:
        '''
        Clears the result to its default value.
        '''
        self.result = 0.0
```

---- Now, interface.py to be rewritten
```## interface.py
import tkinter as tk
from calculator import Calculator

class Interface:
    def __init__(self):
        self.calculator = Calculator()
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.create_widgets()

    def create_widgets(self):
        self.result_var = tk.StringVar()
        self.result_display = tk.Entry(self.root, textvariable=self.result_var, state='readonly', justify='right', font=('Arial', 24))
        self.result_display.grid(row=0, column=0, columnspan=4, sticky='nsew')

        self.entry_number1 = tk.Entry(self.root, justify='right', font=('Arial', 18))
        self.entry_number1.grid(row=1, column=0, columnspan=2, sticky='nsew')

        self.entry_number2 = tk.Entry(self.root, justify='right', font=('Arial', 18))
        self.entry_number2.grid(row=1, column=2, columnspan=2, sticky='nsew')

        self.add_button = tk.Button(self.root, text='+', command=self.add, font=('Arial', 18))
        self.add_button.grid(row=2, column=0, sticky='nsew')

        self.clear_button = tk.Button(self.root, text='C', command=self.clear, font=('Arial', 18))
        self.clear_button.grid(row=2, column=1, sticky='nsew')

        self.quit_button = tk.Button(self.root, text='Quit', command=self.root.quit, font=('Arial', 18))
        self.quit_button.grid(row=2, column=2, columnspan=2, sticky='nsew')

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def start(self):
        self.root.mainloop()

    def display_result(self, result: float):
        self.result_var.set(str(result))

    def get_input(self):
        try:
            number1 = float(self.entry_number1.get())
            number2 = float(self.entry_number2.get())
            return number1, number2
        except ValueError:
            self.show_error("Invalid input! Please enter valid numbers.")
            return None, None

    def add(self):
        number1, number2 = self.get_input()
        if number1 is not None and number2 is not None:
            result = self.calculator.add(number1, number2)
            self.display_result(result)

    def clear(self):
        self.entry_number1.delete(0, tk.END)
        self.entry_number2.delete(0, tk.END)
        self.result_var.set("")

    def show_error(self, message: str):
        tk.messagebox.showerror("Error", message)
```
"""

REFINED_CODE_TEMPLATE = """
NOTICE
Role: You are a professional engineer; The main goal is to complete incremental development by combining legacy code and Guidelines and Incremental Change, ensuring the integration of new features.

# Context
## User New Requirements
{user_requirement}

## Guidelines and Incremental Change
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

# Instruction: Based on the context, follow "Format example", write or rewrite code.
## Write/Rewrite Code: Only write one file {filename}, write or rewrite complete code using triple quotes based on the following attentions and context.
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
4. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
5. Follow Guidelines and Incremental Change: If there is any Incremental Change or Legacy Code files contain "{filename} to be rewritten", you must merge it into the code file according to the guidelines.
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Before using a external variable/module, make sure you import it first.
8. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.
9. Attention: Retain content that is not related to incremental development but important for consistency and clarity.".
"""

WRITE_CODE_GUIDELINE_NODE = ActionNode.from_children("WriteCodeGuideline", [GUIDELINES_AND_INCREMENTAL_CHANGE])


class WriteCodeGuideline(Action):
    async def run(self, context):
        self.llm.system_prompt = "You are a professional software engineer, your primary responsibility is to "
        "meticulously craft comprehensive incremental development guidelines and deliver detailed Incremental Change"
        return await WRITE_CODE_GUIDELINE_NODE.fill(context=context, llm=self.llm, schema="json")


async def main():
    write_code_guideline = WriteCodeGuideline()
    node = await write_code_guideline.run(CODE_GUIDELINE_CONTEXT_EXAMPLE)
    guideline = node.instruct_content.model_dump_json()
    logger.info(guideline)


if __name__ == "__main__":
    asyncio.run(main())

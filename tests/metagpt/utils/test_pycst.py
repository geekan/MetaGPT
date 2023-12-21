from metagpt.utils import pycst

code = """
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import overload

@overload
def add_numbers(a: int, b: int):
    ...

@overload
def add_numbers(a: float, b: float):
    ...

def add_numbers(a: int, b: int):
    return a + b


class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old."
"""

documented_code = '''
"""
This is an example module containing a function and a class definition.
"""


def add_numbers(a: int, b: int):
    """This function is used to add two numbers and return the result.

    Parameters:
        a: The first integer.
        b: The second integer.

    Returns:
        int: The sum of the two numbers.
    """
    return a + b

class Person:
    """This class represents a person's information, including name and age.

    Attributes:
        name: The person's name.
        age: The person's age.
    """

    def __init__(self, name: str, age: int):
        """Creates a new instance of the Person class.

        Parameters:
            name: The person's name.
            age: The person's age.
        """
        ...

    def greet(self):
        """
        Returns a greeting message including the name and age.

        Returns:
            str: The greeting message.
        """
        ...
'''


merged_code = '''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is an example module containing a function and a class definition.
"""

from typing import overload

@overload
def add_numbers(a: int, b: int):
    ...

@overload
def add_numbers(a: float, b: float):
    ...

def add_numbers(a: int, b: int):
    """This function is used to add two numbers and return the result.

    Parameters:
        a: The first integer.
        b: The second integer.

    Returns:
        int: The sum of the two numbers.
    """
    return a + b


class Person:
    """This class represents a person's information, including name and age.

    Attributes:
        name: The person's name.
        age: The person's age.
    """
    def __init__(self, name: str, age: int):
        """Creates a new instance of the Person class.

        Parameters:
            name: The person's name.
            age: The person's age.
        """
        self.name = name
        self.age = age

    def greet(self):
        """
        Returns a greeting message including the name and age.

        Returns:
            str: The greeting message.
        """
        return f"Hello, my name is {self.name} and I am {self.age} years old."
'''


def test_merge_docstring():
    data = pycst.merge_docstring(code, documented_code)
    print(data)
    assert data == merged_code

# -*- coding: utf-8 -*-
# @Date    : 1/11/2024 8:51 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import pytest

from metagpt.actions.di.debug_code import DebugCode
from metagpt.schema import Message

ErrorStr = """Tested passed:

Tests failed:
assert sort_array([1, 5, 2, 3, 4]) == [1, 2, 3, 4, 5] # output: [1, 2, 4, 3, 5]
"""

CODE = """
def sort_array(arr):
    # Helper function to count the number of ones in the binary representation
    def count_ones(n):
        return bin(n).count('1')
    
    # Sort the array using a custom key function
    # The key function returns a tuple (number of ones, value) for each element
    # This ensures that if two elements have the same number of ones, they are sorted by their value
    sorted_arr = sorted(arr, key=lambda x: (count_ones(x), x))
    
    return sorted_arr
```
"""

DebugContext = '''Solve the problem in Python:
def sort_array(arr):
    """
    In this Kata, you have to sort an array of non-negative integers according to
    number of ones in their binary representation in ascending order.
    For similar number of ones, sort based on decimal value.

    It must be implemented like this:
    >>> sort_array([1, 5, 2, 3, 4]) == [1, 2, 3, 4, 5]
    >>> sort_array([-2, -3, -4, -5, -6]) == [-6, -5, -4, -3, -2]
    >>> sort_array([1, 0, 2, 3, 4]) [0, 1, 2, 3, 4]
    """
'''


@pytest.mark.asyncio
async def test_debug_code():
    debug_context = Message(content=DebugContext)
    new_code = await DebugCode().run(context=debug_context, code=CODE, runtime_result=ErrorStr)
    assert "def sort_array(arr)" in new_code["code"]

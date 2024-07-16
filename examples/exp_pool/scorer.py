import asyncio

from metagpt.exp_pool.scorers import SimpleScorer

# Request to implement quicksort in Python
REQ = "Write a program to implement quicksort in python."

# First response: Quicksort implementation without base case
RESP1 = """
def quicksort(arr):
    return quicksort([x for x in arr[1:] if x <= arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x > arr[0]])
"""

# Second response: Quicksort implementation with base case
RESP2 = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    return quicksort([x for x in arr[1:] if x <= arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x > arr[0]])
"""


async def simple():
    """Evaluates two quicksort implementations using SimpleScorer.

    Example:
        {
            "val": 3,
            "reason": "The response attempts to implement quicksort but contains a critical flaw: it lacks a base case to terminate the recursion, which will lead to a maximum recursion depth exceeded error for non-empty lists. Additionally, the function does not handle empty lists properly. A correct implementation should include a base case to handle lists of length 0 or 1."
        }
    """

    scorer = SimpleScorer()

    await scorer.evaluate(req=REQ, resp=RESP1)
    await scorer.evaluate(req=REQ, resp=RESP2)


async def main():
    await simple()


if __name__ == "__main__":
    asyncio.run(main())

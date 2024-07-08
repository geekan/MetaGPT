import asyncio

from metagpt.exp_pool.scorers import SimpleScorer

REQ = "Write a program to implement quicksort in python."

RESP1 = """
def quicksort(arr):
    return quicksort([x for x in arr[1:] if x <= arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x > arr[0]])
"""

RESP2 = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    return quicksort([x for x in arr[1:] if x <= arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x > arr[0]])
"""


async def simple():
    scorer = SimpleScorer()

    await scorer.evaluate(req=REQ, resp=RESP1)
    await scorer.evaluate(req=REQ, resp=RESP2)


async def main():
    await simple()


if __name__ == "__main__":
    asyncio.run(main())

"""This example is from a real issue from MetaGPT: https://github.com/geekan/MetaGPT/issues/1067 with corresponding bugfix as https://github.com/geekan/MetaGPT/pull/1069
We demonstrate that DataInterpreter has the capability to fix such issues.
Prerequisite: You need to manually add the bug back to your local file metagpt/utils/repair_llm_raw_output.py to test DataInterpreter's debugging ability. For detail, please check the issue and PR link above.
"""

import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter

REQ = """
# Requirement
Below is a github issue, solve it. Use Editor to search for the function, understand it, and modify the relevant code.
Write a new test file test.py with Editor and use Terminal to python the test file to ensure you have fixed the issue.
When writing test.py, you should import the function from the file you modified and test it with the given input.
Notice: Don't write all codes in one response, each time, just write code for one step.

# Issue
>> s = "-1"
>> print(extract_state_value_from_output(s))
>> 1
The extract_state_value_from_output function will process -1 into 1,
resulted in an infinite loop for the react mode.
"""


async def main():
    di = DataInterpreter(tools=["Terminal", "Editor"], react_mode="react")
    await di.run(REQ)


if __name__ == "__main__":
    asyncio.run(main())

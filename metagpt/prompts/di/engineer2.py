from metagpt.prompts.di.role_zero import ROLE_INSTRUCTION

EXTRA_INSTRUCTION = """
4. Each time you write a code in your response, write with the Editor directly without preparing a repetitive code block beforehand.
5. Take on ONE task and write ONE code file in each response. DON'T attempt all tasks in one response.
6. When not specified, you should write files in a folder named "src". If you know the project path, then write in a "src" folder under the project path.
7. When provided system design or project schedule, read them first, then adhere to them in your implementation.
"""
ENGINEER2_INSTRUCTION = ROLE_INSTRUCTION + EXTRA_INSTRUCTION.strip()

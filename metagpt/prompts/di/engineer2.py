from metagpt.prompts.di.role_zero import ROLE_INSTRUCTION

EXTRA_INSTRUCTION = """
4. Each time you write a code in your response, write with the Editor directly without preparing a repetitive code block beforehand.
5. Take on ONE task and write ONE code file in each response. DON'T attempt all tasks in one response.
6. When not specified, you should write files in a folder named "src". If you know the project path, then write in a "src" folder under the project path.
7. When provided system design or project schedule, you MUST read them first before making a plan, then adhere to them in your implementation, especially in the programming language, package, or framework. You MUST implement all code files prescribed in the system design or project schedule. You can create a plan first with each task corresponding to implementing one code file.
8. Write at most one file per task, do your best to implement THE ONLY ONE FILE. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
9. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
10. When provided system design, YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
11. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.
12. To modify code in a file, read the entire file, make changes, and update the file with the complete code, ensuring that no line numbers are included in the final write.
13. When a system design or project schedule is provided, at the end of the plan, add a CodeRview Task for each file; for example, if there are three files, add three CodeRview Tasks. For each CodeRview Task, just call ReviewAndRewriteCode.run.
14. When you are making plan.it is hightly recommand to plan all the coding plan and reviews plan in first response.
"""


ENGINEER2_INSTRUCTION = ROLE_INSTRUCTION + EXTRA_INSTRUCTION.strip()

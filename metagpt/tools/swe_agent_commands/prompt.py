from metagpt.tools.swe_agent_commands import DEFAULT_DOCUMENTATION

_SWEAGENT_BASH_DOCS = "\n".join(
    filter(
        lambda x: not x.startswith("submit"),
        DEFAULT_DOCUMENTATION.split("\n"),
    )
)

_COMMAND_DOCS = (
    "\nApart from the standard bash commands, you can also use the following special commands in <execute_bash> environment:\n"
    f"{_SWEAGENT_BASH_DOCS}"
    "Please note that THE EDIT COMMAND REQUIRES PROPER INDENTATION. If you'd like to add the line '        print(x)' you must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run."
)

SWE_AGENT_SYSTEM_TEMPLATE = f"""
SETTING: You are an autonomous programmer, and you're working directly in the command line with a special interface.

The special interface consists of a file editor that shows you {{WINDOW}} lines of a file at a time.
In addition to typical bash commands, you can also use the following commands to help you navigate and edit files.

COMMANDS:
{_COMMAND_DOCS}

Please note that THE EDIT COMMAND REQUIRES PROPER INDENTATION. 
If you'd like to add the line '        print(x)' you must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run.

RESPONSE FORMAT:
Your shell prompt is formatted as follows:
(Open file: <path>) <cwd> $

You need to format your output using two fields; discussion and command.
Your output should always include _one_ discussion and _one_ command field EXACTLY as in the following example:
DISCUSSION
First I'll start by using ls to see what files are in the current directory. Then maybe we can look at some relevant files to see what they look like.
```
ls -a
```

You should only include a *SINGLE* command in the command section and then wait for a response from the shell before continuing with more discussion and commands. Everything you include in the DISCUSSION section will be saved for future reference.
If you'd like to issue two commands at once, PLEASE DO NOT DO THAT! Please instead first submit just the first command, and then after receiving a response you'll be able to issue the second command. 
You're free to use any other bash commands you want (e.g. find, grep, cat, ls, cd) in addition to the special commands listed above.
However, the environment does NOT support interactive session commands (e.g. python, vim), so please do not invoke them.
"""

INSTANCE_TEMPLATE = """
## User Requirement
{user_requirement}

We're currently solving the following issue within our repository. Here's the issue and hints text:
## ISSUE
{issue}

## HINTS
{hints_text}

# INSTRUCTIONS
Now, you're going to solve this issue on your own. Your terminal session has started and you're in the repository's root directory. You can use any bash commands or the special interface to help you. Edit all the files you need to and run any checks that you want. You should NOT modify any existing test case files. If needed, you can add new test cases in a NEW file to reproduce the issue.
Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. You should always wait for feedback after every command. 
When you're satisfied with all of the changes you've made, you can submit your changes to the code base by simply running the submit command.
Note however that you cannot use any interactive session commands (e.g. python, vim) in this environment, but you can write scripts and run them. E.g. you can write a python script and then run it with `python <script_name>.py`.

# NOTE ABOUT THE EDIT COMMAND
Indentation really matters! When editing a file, make sure to insert appropriate indentation before each line! Ensuring the code adheres to PEP8 standards.
"""

IMPORTANT_TIPS = """
IMPORTANT TIPS:
1. Always start by trying to replicate the bug that the issues discusses. 
 If the issue includes code for reproducing the bug, we recommend that you re-implement that in your environment, and run it to make sure you can reproduce the bug.
 Then start trying to fix it.
 When you think you've fixed the bug, re-run the bug reproduction script to make sure that the bug has indeed been fixed.

 If the bug reproduction script does not print anything when it succesfully runs, we recommend adding a print("Script completed successfully, no errors.") command at the end of the file,
 so that you can be sure that the script indeed ran fine all the way through. 

2. If you run a command and it doesn't work, try running a different command. A command that did not work once will not work the second time unless you modify it!

3. If you open a file and need to get to an area around a specific line that is not in the first 100 lines, say line 583, don't just use the scroll_down command multiple times. Instead, use the goto 583 command. It's much quicker. 

4. If the bug reproduction script requires inputting/reading a specific file, such as buggy-input.png, and you'd like to understand how to input that file, conduct a search in the existing repo code, to see whether someone else has already done that. Do this by running the command: find_file "buggy-input.png" If that doensn't work, use the linux 'find' command. 

5. Always make sure to look at the currently open file and the current working directory (which appears right after the currently open file). The currently open file might be in a different directory than the working directory! Note that some commands, such as 'create', open files, so they might change the current  open file.

6. When editing files, it is easy to accidentally specify a wrong line number or to write code with incorrect indentation. Always check the code after you issue an edit to make sure that it reflects what you wanted to accomplish. If it didn't, issue another command to fix it.

"""

# If issue link is provided, add the following line to the instance_template:
TIP_WITH_LINK = "7. It may be necessary to install the repository from source before you can run code. Please think about how to install the environment from the repository directory if you need to do so."

IMPORTANT_TIPS_WITH_LINK = IMPORTANT_TIPS + TIP_WITH_LINK

NEXT_STEP_TEMPLATE = """
# User Requirement and Issue
{user_requirement}

# Observation
{observation}
(Open file: {open_file})
(Current directory: {working_dir})

# Output a json following the format
{output_format}

# Complete Example of Output
It is only used to mimic the output style of the example, please do not copy its content!
-----
{example}
-----
"""

NEXT_STEP_NO_OUTPUT_TEMPLATE = """
Your command ran successfully and did not produce any output.
(Open file: {open_file})
(Current directory: {working_dir})
"""

OUTPUT_FORMAT = """
```json
{{
    "thought": str = "Thought on current situation, reflect on how you should proceed to fulfill the user requirement",
    "bash_command": str = "The next bash command you want to run"
}}
```
"""

EXAMPLE = """
## Step 1 (Required)
```
{
    "thought": "The first step is to search the directory for the `calculator.py` file ...",
    "bash_command": "find_file calculator.py"
}
```
or
```
{
    "thought": "The next step is to search the directory for the `divide` method ...",
    "bash_command": "search_dir divide"
}
```

## Step 2 (Required)
```json
{
    "thought": "The next step is to open the calculator.py file to inspect the divide method. This will help in understanding the current implementation and identifying the bug that needs to be fixed.",
    "bash_command": "open calculator.py"
}
```

## Step 3 (Optional)
```
{
    "thought": "The file has been opened, and now I need to locate the divide method within ...",
    "bash_command": "search_file"
}
```

## Step 4 (Optional)
```
{
  "thought": "Given that the divide method is a part of the Calculator class, I will need to ...",
  "action": "goto 47"
}
```

## Step 5 (Optional)
```
{
  "thought": "Given that the divide method is a part of the Calculator class, I will need to ...",
  "action": "scroll_down"
}
```

## Step 6 (Optional)
```
{
  "thought": "Given that the divide method is a part of the Calculator class, I will need to ...",
  "action": "scroll_up"
}
```

## Step 7 (Required)
```json
{
    "thought": "To address the bug in the divide method of the calculator.py file, I will add a condition to check if the second number (number2) is zero before performing the division. If number2 is zero, I will raise a ValueError to prevent a division by zero error.",
    "bash_command": "edit 47:60 <<EOF\n    def divide(self, number1: float, number2: float) -> float:\n        \"\"\"Divide the first number by the second and return the result.\n\n        Args:\n            number1 (float): The first number.\n            number2 (float): The second number.\n\n        Returns:\n            float: The quotient of the two numbers.\n\n        Raises:\n            ValueError: If the second number is zero.\n        \"\"\"\n        if number2 == 0:\n            raise ValueError(\"The second number cannot be zero.\")\n        return number1 / number2\nEOF"
}
```

## Step 8 (Required)
```json
{
    "thought": "Having successfully fixed the bug ..., the next step is to submit the changes to the repository.",
    "bash_command": "submit"
}
```
"""

INVALID_INPUT_MESSAGE = """
Your command was invalid. Please try again.

If You complete the task, please use the `submit` command to finish the task.
"""

# think about if the task of locating the issue has been completed
ONLY_LOCATE_ISSUE_THINK_PROMPT = """
# User Requirement and Issue
{user_requirement}

# Context
{context}

Output a json following the format:
```json
{{
    "thought": str = "Thought on current situation, reflect on whether you correctly completed the task of locating the code file with the issue.",
    "state": bool = "Decide whether you need to take more actions to complete the task of locating the code file with the issue. Return true if you think so. Return false if you think the task has been completely fulfilled."
    "location" list = "If state is False, provide the location of the code file with the issue. If state is True, provide an empty list."
}}
```
"""

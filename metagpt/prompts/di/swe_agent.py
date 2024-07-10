"""
This code is adapted from the examples provided in the SWE-agent project.
You can find the original examples from the SWE-agent project here:
https://github.com/princeton-nlp/SWE-agent/tree/main/config/configs
"""

SWE_AGENT_SYSTEM_TEMPLATE = """
SETTING: You are an autonomous programmer, and you're working directly in the environment line with a special interface.

The special interface consists of a file editor that shows you 100 lines of a file at a time.

Please note that THE EDIT COMMAND REQUIRES PROPER INDENTATION. Pay attention to the original indentation when replacing the function. 
If you'd like to add the line '        print(x)' you must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run.
Always review your changes post-edit to ensure they accurately reflect your intentions. If the changes are not as desired, don't hesitate to issue another command to correct them.

Your output should always contain a section of reasoning and a command described in JSON format.

Use \\n to represent line breaks, ensuring the command conforms to the JSON format and is displayed on a single line. Except for the `edit` command, each parameter of the command needs to be enclosed in single quotes.
As shown in the example below:

First I'll start by using ls to see what files are in the current directory. Then maybe we can look at some relevant files to see what they look like.

```json
{{
    "command_name": "Bash.run",
    "args": {{
        "cmd": "ls -a" 
    }}
}}
```

You should only include a *SINGLE* command in the command section and then wait for a response from the shell before continuing with more discussion and commands. Everything you include in the DISCUSSION section will be saved for future reference.
If you'd like to issue two commands at once, PLEASE DO NOT DO THAT! Please instead first submit just the first command, and then after receiving a response you'll be able to issue the second command. 
Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. You should always wait for feedback after every command.

You can use any bash commands you want (e.g., find, grep, cat, ls, cd) or any custom special tools (including `edit`) by calling Bash.run. Edit all the files you need.
You should carefully observe the behavior and results of the previous action, and avoid triggering repeated errors.

However, the Bash.run does NOT support interactive session commands (e.g. python, vim), so please do not invoke them.

In addition to the terminal, I also provide additional tools. If provided an issue link, you MUST navigate to the issue page using Browser tool to understand the issue, before starting your fix.

# INSTRUCTIONS:
Your first action must be to check if the repository exists at the current path. If it exists, navigate to the repository path. If the repository doesn't exist, please download it and then navigate to it.
All subsequent actions must be performed within this repository path. Do not leave this directory to execute any actions at any time.
Your terminal session has started, and you can use any bash commands or the special interface to help you. Edit all the files you need.
"""

MINIMAL_EXAMPLE = """
## Example of a actions trajectory
User Requirement and Issue: Fix the bug in the repo. Because the environment is not available, you DO NOT need to run and modify any existing test case files or add new test case files to ensure that the bug is fixed.

### Read and understand issue(Require):
{{
    "command_name": "Browser.goto",
    "args": {{
        "url": "https://github.com/geekan/MetaGPT/issues/1275"
    }}
}}
->

### Locate issue(Require): Locate the issue in the code by searching for the relevant file, function, or class and open the file to view the code.
{{
    "command_name": "Bash.run",
    "args": {{
        "cmd": "cd /workspace/django__django_3.0"
    }}
}}
->

Bash.run(cmd='search_dir_and_preview ASCIIUsernameValidator')
{{
    "command_name": "Bash.run",
    "args": {{
        "cmd": "open /workspace/django__django_3.0/django/contrib/auth/validators.py"   
    }}
}}
->

### Fix the Bug(Require): Fix the bug in the code by editing the relevant function, class or code snippet.
{{
    "command_name": "Bash.run",
    "args": {{
        "cmd": "edit 10:20 <<EOF\n    regex = r'\A[\w.@+-]+\Z'\n    message = _( \n        'Enter a valid username. This value may contain only English letters, ' \n        'numbers, and @/./+/-/_ characters.'\n    )\n    flags = re.ASCII\n\n@deconstructible\nclass UnicodeUsernameValidator(validators.RegexValidator):\n    regex = r'\A[\w.@+-]+\Z'\nEOF"
    }}
}}
->

### Submit the Changes(Require): Submit the changes to the repository.
{{
    "command_name": "Bash.run",
    "args": {{
        "cmd": "submit"
    }}
}}
Bash.run(cmd='submit')
->
{{
    "command_name": "end",
}}
"""


IMPORTANT_TIPS = """
1. If you run a command and it doesn't work, try running a different command. A command that did not work once will not work the second time unless you modify it! 

2. If you open a file and need to get to an area around a specific line that is not in the first 100 lines, say line 583, don't just use the scroll_down command multiple times. Instead, use the goto 583 command. It's much quicker. 

3. Always make sure to look at the currently open file and the current working directory (which appears right after the currently open file). The currently open file might be in a different directory than the working directory! Note that some commands, such as 'create', open files, so they might change the current  open file.

4. When editing files, it is easy to accidentally specify a wrong line number or to write code with incorrect indentation. Always check the code after you issue an edit to make sure that it reflects what you wanted to accomplish. If it didn't, issue another command to fix it.

5. After editing, verify the changes to ensure correct line numbers and proper indentation. Adhere to PEP8 standards for Python code.

6. NOTE ABOUT THE EDIT COMMAND: Indentation really matters! When editing a file, make sure to insert appropriate indentation before each line! Ensuring the code adheres to PEP8 standards. If a edit command fails, you can try to edit the file again to correct the indentation, but don't repeat the same command without changes.

7. YOU CAN ONLY ENTER ONE COMMAND AT A TIME and must wait for feedback, plan your commands carefully. 

8. You cannot use any interactive session commands (e.g. python, vim) in this environment, but you can write scripts and run them. E.g. you can write a python script and then run it with `python <script_name>.py`.

9. To avoid syntax errors when editing files multiple times, consider opening the file to view the surrounding code related to the error line and make modifications based on this context.

10. When using the `edit` command, remember it operates within a closed range. This is crucial to prevent accidental deletion of non-targeted code during code replacement.

11. Ensure to observe the currently open file and the current working directory, which is displayed right after the open file. The open file might be in a different directory than the working directory. Remember, commands like 'create' open files and might alter the current open file.

12. Effectively using Use search commands (`search_dir`, `search_file`, `find_file`) and navigation commands (`open`, `goto`) to locate and modify files efficiently. Follow these steps and considerations for optimal results:

    **General Search Guidelines:**
    - Ensure you are in the repository's root directory before starting your search.
    - Always double-check the current working directory and the currently open file to avoid confusion.
    - Avoid repeating failed search commands without modifications to improve efficiency.

    **Strategies for Searching and Navigating Files:**

    1. **If you know the file's location:**
       - Use the `open` command directly to open the file.
       - Use `search_file` to find the `search_term` within the currently open file.
       - Alternatively, use the `goto` command to jump to the specified line.
       - **Boundary Consideration:** Ensure the file path is correctly specified and accessible.

    2. **If you know the filename but not the exact location:**
       - Use `find_file` to locate the file in the directory.
       - Use `open` to open the file once located.
       - Use `search_file` to find the `search_term` within the file.
       - Use `goto` to jump to the specified line if needed.
       - **Boundary Consideration:** Handle cases where the file may exist in multiple directories by verifying the correct path before opening.

    3. **If you know the symbol but not the file's location:**
       - Use `search_dir_and_preview` to find files containing the symbol within the directory.
       - Review the search results to identify the relevant file(s).
       - Use `open` to open the identified file.
       - Use `search_file` to locate the `search_term` within the open file.
       - Use `goto` to jump to the specified line.
       - **Boundary Consideration:** Be thorough in reviewing multiple search results to ensure you open the correct file. Consider using more specific search terms if initial searches return too many results.

    **Search Tips:**
    - The `<search_term>` for `search_dir_and_preview`, `find_file`, or `search_file` should be an existing class name, function name, or file name.
    - Enclose terms like `def` or `class` in quotes when searching for functions or classes (e.g., `search_dir_and_preview 'def apow'` or `search_file 'class Pow'`).
    - Use wildcard characters (`*`, `?`) in search terms to broaden or narrow down your search scope.
    - If search commands return too many results, refine your search criteria or use more specific terms.
    - If a search command fails, modify the search criteria and check for typos or incorrect paths, then try again.
    - Based on feedback of observation or bash command in trajectory to guide adjustments in your search strategy.

13. If the task results in succeed, fail, or NO PROGRESS, output `submit`.

14. If provided an issue link, you MUST go to the issue page using Browser tool to understand the issue before starting your fix.

15. When the edit fails, try to enlarge the starting line.
"""

NEXT_STEP_TEMPLATE = f"""
# Example of Output
These examples are provided to demonstrate the output style that expected to be several stages including Locate issue, Fix the bug, Test the fix(Optional), and Submit the changes. It is included to show you how to correctly use the interface. You do not need to follow exactly what is done in the Example. The separator is "-----".
----- Beginning of Examples -----
{MINIMAL_EXAMPLE}
----- End of Examples -----

# IMPORTANT TIPS
{IMPORTANT_TIPS}

# Output Next Step
The current bash state is:
(Open file: {{open_file}})
(Current directory: {{working_dir}})

Avoid repeating the same command. Instead, please think about the current situation and provide the next bash command to execute in JSON format:"

"""

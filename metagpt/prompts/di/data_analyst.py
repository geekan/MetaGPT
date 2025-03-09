from metagpt.strategy.task_type import TaskType

EXTRA_INSTRUCTION = """
6. Carefully consider how you handle web tasks:
 - Use SearchEnhancedQA for general information searching, i.e. querying search engines, such as googling news, weather, wiki, etc. Usually, no link is provided.
 - Use Browser for reading, navigating, or in-domain searching within a specific web, such as reading a blog, searching products from a given e-commerce web link, or interacting with a web app.
 - Use DataAnalyst.write_and_execute_code for web scraping, such as gathering batch data or info from a provided link.
 - Write code to view the HTML content rather than using the Browser tool.
 - Make sure the command_name are certainly in Available Commands when you use the Browser tool.
7. When you are making plan. It is highly recommend to plan and append all the tasks in first response once time, except for 7.1.
7.1. When the requirement is inquiring about a pdf, docx, md, or txt document, read the document first through either Editor.read WITHOUT a plan. After reading the document, use RoleZero.reply_to_human if the requirement can be answered straightaway, otherwise, make a plan if further calculation is needed.
8. Don't finish_current_task multiple times for the same task.
9. Finish current task timely, such as when the code is written and executed successfully.
10. When using the command 'end', add the command 'finish_current_task' before it.
"""

TASK_TYPE_DESC = "\n".join([f"- **{tt.type_name}**: {tt.value.desc}" for tt in TaskType])


CODE_STATUS = """
**Code written**:
{code}

**Execution status**: {status}
**Execution result**: {result}
"""

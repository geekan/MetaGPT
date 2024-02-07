# -*- encoding: utf-8 -*-
"""
@Date    :   2024/02/07 
@Author  :   Tuo Zhou
@File    :   email_summary.py
"""

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main():
    # prompt_response = """I will give you your Outlook email account(englishgpt@outlook.com) and password(the outlook_email_password item in the environment variable). You need to find the latest email in my inbox with the sender's suffix @qq.com and reply to him "Thank you! I have received your email~"""""
    prompt_summary = """I will give you your Outlook email account(englishgpt@outlook.com) and password(outlook_email_password item in the environment variable).
            Firstly, Please help me present the latest 5 senders and full letter contents.
            Then, summarize each of the 5 emails into one sentence with Chinese(you can do this by yourself, don't need import other models to do this) and output them in a markdown format."""
    # ci_response = CodeInterpreter(goal=prompt_response, use_tools=True)
    ci_summary = CodeInterpreter(goal=prompt_summary, use_tools=True)

    await ci_summary.run(prompt_summary)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

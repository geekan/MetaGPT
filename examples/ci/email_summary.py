# -*- encoding: utf-8 -*-
"""
@Date    :   2024/02/07 
@Author  :   Tuo Zhou
@File    :   email_summary.py
"""

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main():
    # For email response prompt
    email_account = "your_email_account"
    # prompt = f"""I will give you your Outlook email account({email_account}) and password(email_password item in the environment variable). You need to find the latest email in my inbox with the sender's suffix @qq.com and reply to him "Thank you! I have received your email~"""""
    prompt = f"""I will give you your Outlook email account({email_account}) and password(email_password item in the environment variable).
            Firstly, Please help me fetch the latest 5 senders and full letter contents.
            Then, summarize each of the 5 emails into one sentence(you can do this by yourself, no need import other models to do this) and output them in a markdown format."""

    ci = CodeInterpreter(use_tools=True)

    await ci.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

# -*- encoding: utf-8 -*-
"""
@Date    :   2024/02/07 
@Author  :   Tuo Zhou
@File    :   email_summary.py
"""
import os

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    email_account = "your_email_account"
    # your password will stay only on your device and not go to LLM api
    os.environ["email_password"] = "your_email_password"

    ### Prompt for automatic email reply, uncomment to try this too ###
    # prompt = f"""I will give you your Outlook email account ({email_account}) and password (email_password item in the environment variable). You need to find the latest email in my inbox with the sender's suffix @gmail.com and reply "Thank you! I have received your email~"""""

    ### Prompt for automatic email summary ###
    prompt = f"""I will give you your Outlook email account ({email_account}) and password (email_password item in the environment variable).
            Firstly, Please help me fetch the latest 5 senders and full letter contents.
            Then, summarize each of the 5 emails into one sentence (you can do this by yourself, no need to import other models to do this) and output them in a markdown format."""

    di = DataInterpreter()

    await di.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

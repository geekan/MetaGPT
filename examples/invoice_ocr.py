#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 21:40:57
@Author  : Stitch-z
@File    : invoice_ocr.py
"""

import asyncio
import os

from metagpt.roles.invoice_ocr_assistant import InvoiceOCRAssistant
from metagpt.schema import Message


async def main():
    relative_paths = [
        "../tests/data/invoices/invoice-1.pdf",
        "../tests/data/invoices/invoice-2.png",
        "../tests/data/invoices/invoice-3.jpg",
        "../tests/data/invoices/invoice-4.zip"
    ]
    # Get the current working directory
    current_directory = os.getcwd()
    # The absolute path of the file
    absolute_file_paths = [os.path.abspath(os.path.join(current_directory, path)) for path in relative_paths]

    for path in absolute_file_paths:
        role = InvoiceOCRAssistant()
        await role.run(Message(
            content="Invoicing date",
            instruct_content={"file_path": path}
        ))


if __name__ == '__main__':
    asyncio.run(main())


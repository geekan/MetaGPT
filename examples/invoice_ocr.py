#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 21:40:57
@Author  : Stitch-z
@File    : invoice_ocr.py
"""

import asyncio
from pathlib import Path

from metagpt.roles.invoice_ocr_assistant import InvoiceOCRAssistant, InvoicePath
from metagpt.schema import Message


async def main():
    relative_paths = [
        Path("../tests/data/invoices/invoice-1.pdf"),
        Path("../tests/data/invoices/invoice-2.png"),
        Path("../tests/data/invoices/invoice-3.jpg"),
        Path("../tests/data/invoices/invoice-4.zip"),
    ]
    # The absolute path of the file
    absolute_file_paths = [Path.cwd() / path for path in relative_paths]

    for path in absolute_file_paths:
        role = InvoiceOCRAssistant()
        await role.run(Message(content="Invoicing date", instruct_content=InvoicePath(file_path=path)))


if __name__ == "__main__":
    asyncio.run(main())

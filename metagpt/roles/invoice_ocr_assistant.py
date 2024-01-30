#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 14:10:05
@Author  : Stitch-z
@File    : invoice_ocr_assistant.py
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from metagpt.actions.invoice_ocr import GenerateTable, InvoiceOCR, ReplyQuestion
from metagpt.prompts.invoice_ocr import INVOICE_OCR_SUCCESS
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


class InvoicePath(BaseModel):
    file_path: Path = ""


class OCRResults(BaseModel):
    ocr_result: str = "[]"


class InvoiceData(BaseModel):
    invoice_data: list[dict] = []


class ReplyData(BaseModel):
    content: str = ""


class InvoiceOCRAssistant(Role):
    """Invoice OCR assistant, support OCR text recognition of invoice PDF, png, jpg, and zip files,
    generate a table for the payee, city, total amount, and invoicing date of the invoice,
    and ask questions for a single file based on the OCR recognition results of the invoice.

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the invoice table will be generated.
    """

    name: str = "Stitch"
    profile: str = "Invoice OCR Assistant"
    goal: str = "OCR identifies invoice files and generates invoice main information table"
    constraints: str = ""
    language: str = "ch"
    filename: str = ""
    origin_query: str = ""
    orc_data: Optional[list] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([InvoiceOCR])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        msg = self.rc.memory.get(k=1)[0]
        todo = self.rc.todo
        if isinstance(todo, InvoiceOCR):
            self.origin_query = msg.content
            invoice_path: InvoicePath = msg.instruct_content
            file_path = invoice_path.file_path
            self.filename = file_path.name
            if not file_path:
                raise Exception("Invoice file not uploaded")

            resp = await todo.run(file_path)
            if len(resp) == 1:
                # Single file support for questioning based on OCR recognition results
                self.set_actions([GenerateTable, ReplyQuestion])
                self.orc_data = resp[0]
            else:
                self.set_actions([GenerateTable])

            self.set_todo(None)
            content = INVOICE_OCR_SUCCESS
            resp = OCRResults(ocr_result=json.dumps(resp))
            msg = Message(content=content, instruct_content=resp)
            self.rc.memory.add(msg)
            return await super().react()
        elif isinstance(todo, GenerateTable):
            ocr_results: OCRResults = msg.instruct_content
            resp = await todo.run(json.loads(ocr_results.ocr_result), self.filename)

            # Convert list to Markdown format string
            df = pd.DataFrame(resp)
            markdown_table = df.to_markdown(index=False)
            content = f"{markdown_table}\n\n\n"
            resp = InvoiceData(invoice_data=resp)
        else:
            resp = await todo.run(self.origin_query, self.orc_data)
            content = resp
            resp = ReplyData(content=resp)

        msg = Message(content=content, instruct_content=resp)
        self.rc.memory.add(msg)
        return msg

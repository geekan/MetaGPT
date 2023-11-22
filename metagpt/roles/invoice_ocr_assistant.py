#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 14:10:05
@Author  : Stitch-z
@File    : invoice_ocr_assistant.py
"""

import pandas as pd

from metagpt.actions.invoice_ocr import InvoiceOCR, GenerateTable, ReplyQuestion
from metagpt.prompts.invoice_ocr import INVOICE_OCR_SUCCESS
from metagpt.roles import Role
from metagpt.schema import Message


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

    def __init__(
        self,
        name: str = "Stitch",
        profile: str = "Invoice OCR Assistant",
        goal: str = "OCR identifies invoice files and generates invoice main information table",
        constraints: str = "",
        language: str = "ch",
    ):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([InvoiceOCR])
        self.language = language
        self.filename = ""
        self.origin_query = ""
        self.orc_data = None
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        msg = self._rc.memory.get(k=1)[0]
        todo = self._rc.todo
        if isinstance(todo, InvoiceOCR):
            self.origin_query = msg.content
            file_path = msg.instruct_content.get("file_path")
            self.filename = file_path.name
            if not file_path:
                raise Exception("Invoice file not uploaded")

            resp = await todo.run(file_path)
            if len(resp) == 1:
                # Single file support for questioning based on OCR recognition results
                self._init_actions([GenerateTable, ReplyQuestion])
                self.orc_data = resp[0]
            else:
                self._init_actions([GenerateTable])

            self._rc.todo = None
            content = INVOICE_OCR_SUCCESS
        elif isinstance(todo, GenerateTable):
            ocr_results = msg.instruct_content
            resp = await todo.run(ocr_results, self.filename)

            # Convert list to Markdown format string
            df = pd.DataFrame(resp)
            markdown_table = df.to_markdown(index=False)
            content = f"{markdown_table}\n\n\n"
        else:
            resp = await todo.run(self.origin_query, self.orc_data)
            content = resp

        msg = Message(content=content, instruct_content=resp)
        self._rc.memory.add(msg)
        return msg

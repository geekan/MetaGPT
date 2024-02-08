#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 23:11:27
@Author  : Stitch-z
@File    : test_invoice_ocr_assistant.py
"""

from pathlib import Path

import pandas as pd
import pytest

from metagpt.const import DATA_PATH, TEST_DATA_PATH
from metagpt.roles.invoice_ocr_assistant import InvoiceOCRAssistant, InvoicePath
from metagpt.schema import Message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "invoice_path", "invoice_table_path", "expected_result"),
    [
        (
            "Invoicing date",
            Path("invoices/invoice-1.pdf"),
            Path("invoice_table/invoice-1.xlsx"),
            {"收款人": "小明", "城市": "深圳", "总费用/元": 412.00, "开票日期": "2023年02月03日"},
        ),
        (
            "Invoicing date",
            Path("invoices/invoice-2.png"),
            Path("invoice_table/invoice-2.xlsx"),
            {"收款人": "铁头", "城市": "广州", "总费用/元": 898.00, "开票日期": "2023年03月17日"},
        ),
        (
            "Invoicing date",
            Path("invoices/invoice-3.jpg"),
            Path("invoice_table/invoice-3.xlsx"),
            {"收款人": "夏天", "城市": "福州", "总费用/元": 2462.00, "开票日期": "2023年08月26日"},
        ),
    ],
)
async def test_invoice_ocr_assistant(
    query: str, invoice_path: Path, invoice_table_path: Path, expected_result: dict, context
):
    invoice_path = TEST_DATA_PATH / invoice_path
    role = InvoiceOCRAssistant(context=context)
    await role.run(Message(content=query, instruct_content=InvoicePath(file_path=invoice_path)))
    invoice_table_path = DATA_PATH / invoice_table_path
    df = pd.read_excel(invoice_table_path)
    resp = df.to_dict(orient="records")
    assert isinstance(resp, list)
    assert len(resp) == 1
    resp = resp[0]
    assert expected_result["收款人"] == resp["收款人"]
    assert expected_result["城市"] in resp["城市"]
    assert float(expected_result["总费用/元"]) == float(resp["总费用/元"])
    assert expected_result["开票日期"] == resp["开票日期"]

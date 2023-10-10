#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 23:11:27
@Author  : Stitch-z
@File    : test_invoice_ocr_assistant.py
"""

import os
import pandas as pd
from typing import List

import pytest

from metagpt.roles.invoice_ocr_assistant import InvoiceOCRAssistant
from metagpt.schema import Message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "invoice_path", "invoice_table_path", "expected_result"),
    [
        (
            "Invoicing date",
            "../../data/invoices/invoice-1.pdf",
            "../../../data/invoice_table/invoice-1.xlsx",
            [
                {
                    "收款人": "小明",
                    "城市": "深圳市",
                    "总费用/元": 412.00,
                    "开票日期": "2023年02月03日"
                }
            ]
        ),
        (
            "Invoicing date",
            "../../data/invoices/invoice-2.png",
            "../../../data/invoice_table/invoice-2.xlsx",
            [
                {
                    "收款人": "铁头",
                    "城市": "广州市",
                    "总费用/元": 898.00,
                    "开票日期": "2023年03月17日"
                }
            ]
        ),
        (
            "Invoicing date",
            "../../data/invoices/invoice-3.jpg",
            "../../../data/invoice_table/invoice-3.xlsx",
            [
                {
                    "收款人": "夏天",
                    "城市": "福州市",
                    "总费用/元": 2462.00,
                    "开票日期": "2023年08月26日"
                }
            ]
        ),
        (
            "Invoicing date",
            "../../data/invoices/invoice-4.zip",
            "../../../data/invoice_table/invoice-4.xlsx",
            [
                {
                    "收款人": "小明",
                    "城市": "深圳市",
                    "总费用/元": 412.00,
                    "开票日期": "2023年02月03日"
                },
                {
                    "收款人": "铁头",
                    "城市": "广州市",
                    "总费用/元": 898.00,
                    "开票日期": "2023年03月17日"
                },
                {
                    "收款人": "夏天",
                    "城市": "福州市",
                    "总费用/元": 2462.00,
                    "开票日期": "2023年08月26日"
                }
            ]
        ),
    ]
)
async def test_invoice_ocr_assistant(
    query: str,
    invoice_path: str,
    invoice_table_path: str,
    expected_result: List[dict]
):
    invoice_path = os.path.abspath(os.path.join(os.getcwd(), invoice_path))
    role = InvoiceOCRAssistant()
    await role.run(Message(
        content=query,
        instruct_content={"file_path": invoice_path}
    ))
    invoice_table_path = os.path.abspath(os.path.join(os.getcwd(), invoice_table_path))
    df = pd.read_excel(invoice_table_path)
    dict_result = df.to_dict(orient='records')
    assert dict_result == expected_result


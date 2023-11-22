#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/10/09 18:40:34
@Author  : Stitch-z
@File    : test_invoice_ocr.py
"""

import os
from typing import List

import pytest
from pathlib import Path

from metagpt.actions.invoice_ocr import InvoiceOCR, GenerateTable, ReplyQuestion


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invoice_path",
    [
        "../../data/invoices/invoice-3.jpg",
        "../../data/invoices/invoice-4.zip",
    ]
)
async def test_invoice_ocr(invoice_path: str):
    invoice_path = os.path.abspath(os.path.join(os.getcwd(), invoice_path))
    filename = os.path.basename(invoice_path)
    resp = await InvoiceOCR().run(file_path=Path(invoice_path), filename=filename)
    assert isinstance(resp, list)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("invoice_path", "expected_result"),
    [
        (
            "../../data/invoices/invoice-1.pdf",
            [
                {
                    "收款人": "小明",
                    "城市": "深圳市",
                    "总费用/元": "412.00",
                    "开票日期": "2023年02月03日"
                }
            ]
        ),
    ]
)
async def test_generate_table(invoice_path: str, expected_result: list[dict]):
    invoice_path = os.path.abspath(os.path.join(os.getcwd(), invoice_path))
    filename = os.path.basename(invoice_path)
    ocr_result = await InvoiceOCR().run(file_path=Path(invoice_path), filename=filename)
    table_data = await GenerateTable().run(ocr_results=ocr_result, filename=filename)
    assert table_data == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("invoice_path", "query", "expected_result"),
    [
        ("../../data/invoices/invoice-1.pdf", "Invoicing date", "2023年02月03日")
    ]
)
async def test_reply_question(invoice_path: str, query: dict, expected_result: str):
    invoice_path = os.path.abspath(os.path.join(os.getcwd(), invoice_path))
    filename = os.path.basename(invoice_path)
    ocr_result = await InvoiceOCR().run(file_path=Path(invoice_path), filename=filename)
    result = await ReplyQuestion().run(query=query, ocr_result=ocr_result)
    assert expected_result in result


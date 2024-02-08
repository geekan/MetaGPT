#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/10/09 18:40:34
@Author  : Stitch-z
@File    : test_invoice_ocr.py
"""

from pathlib import Path

import pytest

from metagpt.actions.invoice_ocr import GenerateTable, InvoiceOCR, ReplyQuestion
from metagpt.const import TEST_DATA_PATH


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invoice_path",
    [
        Path("invoices/invoice-3.jpg"),
        Path("invoices/invoice-4.zip"),
    ],
)
async def test_invoice_ocr(invoice_path: Path, context):
    invoice_path = TEST_DATA_PATH / invoice_path
    resp = await InvoiceOCR(context=context).run(file_path=Path(invoice_path))
    assert isinstance(resp, list)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("invoice_path", "expected_result"),
    [
        (Path("invoices/invoice-1.pdf"), {"收款人": "小明", "城市": "深圳", "总费用/元": 412.00, "开票日期": "2023年02月03日"}),
    ],
)
async def test_generate_table(invoice_path: Path, expected_result: dict):
    invoice_path = TEST_DATA_PATH / invoice_path
    filename = invoice_path.name
    ocr_result = await InvoiceOCR().run(file_path=Path(invoice_path))
    table_data = await GenerateTable().run(ocr_results=ocr_result, filename=filename)
    assert isinstance(table_data, list)
    table_data = table_data[0]
    assert expected_result["收款人"] == table_data["收款人"]
    assert expected_result["城市"] in table_data["城市"]
    assert float(expected_result["总费用/元"]) == float(table_data["总费用/元"])
    assert expected_result["开票日期"] == table_data["开票日期"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("invoice_path", "query", "expected_result"),
    [(Path("invoices/invoice-1.pdf"), "Invoicing date", "2023年02月03日")],
)
async def test_reply_question(invoice_path: Path, query: dict, expected_result: str):
    invoice_path = TEST_DATA_PATH / invoice_path
    ocr_result = await InvoiceOCR().run(file_path=Path(invoice_path))
    result = await ReplyQuestion().run(query=query, ocr_result=ocr_result)
    assert expected_result in result

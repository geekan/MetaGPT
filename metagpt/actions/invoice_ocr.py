#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/21 18:10:20
@Author  : Stitch-z
@File    : invoice_ocr.py
@Describe : Actions of the invoice ocr assistant.
"""

import os
import zipfile
from enum import Enum
from pathlib import Path

import pandas as pd

from typing import Dict, List
from paddleocr import PaddleOCR

from metagpt.actions import Action
from metagpt.const import INVOICE_OCR_TABLE_PATH
from metagpt.logs import logger
from metagpt.prompts.invoice_ocr import EXTRACT_OCR_MAIN_INFO_PROMPT, REPLY_OCR_QUESTION_PROMPT
from metagpt.utils.common import OutputParser
from metagpt.utils.file import File


class FileExtensionType(Enum):
    """Enum representing file extensions and their associated types.
    Each enum member consists of a tuple containing the file extension and its associated type.

    """

    ZIP = (".zip", "zip")
    PDF = (".pdf", "pdf")
    PNG = (".png", "png")
    JPG = (".jpg", "jpg")

    @classmethod
    def get_extension_list(cls) -> List[str]:
        """Get a list of file extensions.

        Returns:
            A list of file extensions as strings.
        """
        return [ext.value[0] for ext in cls]

    @classmethod
    def get_type_list(cls) -> List[str]:
        """Get a list of file types.

        Returns:
            A list of file types as strings.
        """
        return [ext.value[1] for ext in cls]


class InvoiceOCR(Action):
    """Action class for performing OCR on invoice files, including zip, PDF, png, and jpg files.

    Args:
        name: The name of the action. Defaults to an empty string.
        language: The language for OCR output. Defaults to "ch" (Chinese).

    """

    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @staticmethod
    async def _check_file_type(filename: str) -> str:
        """Check the file type of the given filename.

        Args:
            filename: The name of the file.

        Returns:
            The file type based on FileExtensionType enum.

        Raises:
            Exception: If the file format is not zip, pdf, png, or jpg.
        """
        file_ext = None
        for ext in FileExtensionType:
            if filename.endswith(ext.value[0]):
                file_ext = ext.value[1]
                break

        if not file_ext:
            raise Exception("The invoice format is not zip, pdf, png, or jpg")

        return file_ext

    @staticmethod
    async def _unzip(file_path: Path) -> Path:
        """Unzip a file and return the path to the unzipped directory.

        Args:
            file_path: The path to the zip file.

        Returns:
            The path to the unzipped directory.
        """
        file_directory = file_path.parent
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                # Use CP437 to encode the file name, and then use GBK decoding to prevent Chinese garbled code
                relative_name = zip_info.filename.encode('cp437').decode('gbk')
                unzip_dir, name = relative_name.split("/")
                if name:
                    full_filename = file_directory / relative_name
                    await File.write(full_filename.parent, name, zip_ref.read(zip_info.filename))

        unzip_path = file_directory / unzip_dir
        logger.info(f"unzip_path: {unzip_path}")
        return unzip_path

    async def run(self, file_path: Path, filename: str, *args, **kwargs) -> list:
        """Execute the action to identify invoice files through OCR.

        Args:
            file_path: The path to the input file.
            filename: The name of the input file.

        Returns:
            A list of OCR results.
        """
        file_ext = await self._check_file_type(filename)

        if file_ext == FileExtensionType.ZIP.value[1]:
            # OCR recognizes zip batch files
            unzip_path = await self._unzip(file_path)
            file_list = os.listdir(unzip_path)
            ocr_list = []

            for filename in file_list:
                invoice_file_path = unzip_path / filename
                # Identify files that match the type
                if filename.split(".")[-1] in FileExtensionType.get_type_list():
                    ocr = PaddleOCR(use_angle_cls=True, lang="ch", page_num=1)
                    ocr_result = ocr.ocr(str(invoice_file_path), cls=True)
                    ocr_list.append(ocr_result)
            return ocr_list

        else:
            #  OCR identifies single file
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", page_num=1)
            ocr_result = ocr.ocr(str(file_path), cls=True)
            return [ocr_result]


class GenerateTable(Action):
    """Action class for generating tables from OCR results.

    Args:
        name: The name of the action. Defaults to an empty string.
        language: The language used for the generated table. Defaults to "ch" (Chinese).

    """

    def __init__(self, name: str = "", language: str = "ch", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.language = language

    async def run(self, ocr_results: list, filename: str, *args, **kwargs) -> Dict[str, str]:
        """Processes OCR results, extracts invoice information, generates a table, and saves it as an Excel file.

        Args:
            ocr_results: A list of OCR results obtained from invoice processing.
            filename: The name of the output Excel file.

        Returns:
            A dictionary containing the invoice information.

        """
        table_data = []
        pathname = INVOICE_OCR_TABLE_PATH
        pathname.mkdir(parents=True, exist_ok=True)

        for ocr_result in ocr_results:
            # Extract invoice OCR main information
            prompt = EXTRACT_OCR_MAIN_INFO_PROMPT.format(ocr_result=ocr_result, language=self.language)
            ocr_info = await self._aask(prompt=prompt)
            invoice_data = OutputParser.extract_struct(ocr_info, dict)
            if invoice_data:
                table_data.append(invoice_data)

        # Generate Excel file
        filename = f"{filename.split('.')[0]}.xlsx"
        full_filename = f"{pathname}/{filename}"
        df = pd.DataFrame(table_data)
        df.to_excel(full_filename, index=False)
        return table_data


class ReplyQuestion(Action):
    """Action class for generating replies to questions based on OCR results.

    Args:
        name: The name of the action. Defaults to an empty string.
        language: The language used for generating the reply. Defaults to "ch" (Chinese).

    """

    def __init__(self, name: str = "", language: str = "ch", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.language = language

    async def run(self, query: str, ocr_result: list, *args, **kwargs) -> str:
        """Reply to questions based on ocr results.

        Args:
            query: The question for which a reply is generated.
            ocr_result: A list of OCR results.

        Returns:
            A reply result of string type.
        """
        prompt = REPLY_OCR_QUESTION_PROMPT.format(query=query, ocr_result=ocr_result, language=self.language)
        resp = await self._aask(prompt=prompt)
        return resp


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/8 14:03
@Author  : alexanderwu
@File    : document.py
"""
from pathlib import Path

import pandas as pd
from langchain.document_loaders import (
    TextLoader,
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import CharacterTextSplitter
from tqdm import tqdm


def validate_cols(content_col: str, df: pd.DataFrame):
    if content_col not in df.columns:
        raise ValueError


def read_data(data_path: Path):
    suffix = data_path.suffix
    if '.xlsx' == suffix:
        data = pd.read_excel(data_path)
    elif '.csv' == suffix:
        data = pd.read_csv(data_path)
    elif '.json' == suffix:
        data = pd.read_json(data_path)
    elif suffix in ('.docx', '.doc'):
        data = UnstructuredWordDocumentLoader(str(data_path), mode='elements').load()
    elif '.txt' == suffix:
        data = TextLoader(str(data_path)).load()
        text_splitter = CharacterTextSplitter(separator='\n', chunk_size=256, chunk_overlap=0)
        texts = text_splitter.split_documents(data)
        data = texts
    elif '.pdf' == suffix:
        data = UnstructuredPDFLoader(str(data_path), mode="elements").load()
    else:
        raise NotImplementedError
    return data


class Document:

    def __init__(self, data_path, content_col='content', meta_col='metadata'):
        self.data = read_data(data_path)
        if isinstance(self.data, pd.DataFrame):
            validate_cols(content_col, self.data)
        self.content_col = content_col
        self.meta_col = meta_col

    def _get_docs_and_metadatas_by_df(self) -> (list, list):
        df = self.data
        docs = []
        metadatas = []
        for i in tqdm(range(len(df))):
            docs.append(df[self.content_col].iloc[i])
            if self.meta_col:
                metadatas.append({self.meta_col: df[self.meta_col].iloc[i]})
            else:
                metadatas.append({})

        return docs, metadatas

    def _get_docs_and_metadatas_by_langchain(self) -> (list, list):
        data = self.data
        docs = [i.page_content for i in data]
        metadatas = [i.metadata for i in data]
        return docs, metadatas

    def get_docs_and_metadatas(self) -> (list, list):
        if isinstance(self.data, pd.DataFrame):
            return self._get_docs_and_metadatas_by_df()
        elif isinstance(self.data, list):
            return self._get_docs_and_metadatas_by_langchain()
        else:
            raise NotImplementedError
        
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/8 14:03
@Author  : alexanderwu
@File    : document.py
"""

from typing import Union, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import pandas as pd
from langchain.document_loaders import (
    TextLoader,
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import CharacterTextSplitter
from tqdm import tqdm

from metagpt.logs import logger


def validate_cols(content_col: str, df: pd.DataFrame):
    if content_col not in df.columns:
        raise ValueError("Content column not found in DataFrame.")


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
        raise NotImplementedError("File format not supported.")
    return data


class Document(BaseModel):
    """
    Document: Handles operations related to document files.
    """
    content: str = Field(default='')
    file_path: Path = Field(default=None)

    @classmethod
    def from_path(cls, file_path: Path):
        """
        Create a Document instance from a file path.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        content = file_path.read_text()
        return cls(content=content, file_path=file_path)

    @classmethod
    def from_text(cls, text: str, file_path: Optional[Path] = None):
        """
        Create a Document from a text string.
        """
        return cls(content=text, file_path=file_path)

    def to_path(self, file_path: Optional[Path] = None):
        """
        Save content to the specified file path.
        """
        if file_path is not None:
            self.file_path = file_path

        if self.file_path is None:
            raise ValueError("File path is not set.")

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(self.content)

    def persist(self):
        """
        Persist document to disk.
        """
        return self.to_path()


class IndexableDocument(Document):
    """
    Advanced document handling: For vector databases or search engines.
    """
    data: Union[pd.DataFrame, list]
    content_col: Optional[str] = Field(default='')
    meta_col: Optional[str] = Field(default='')

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_path(cls, data_path: Path, content_col='content', meta_col='metadata'):
        if not data_path.exists():
            raise FileNotFoundError(f"File {data_path} not found.")
        data = read_data(data_path)
        content = data_path.read_text()
        if isinstance(data, pd.DataFrame):
            validate_cols(content_col, data)
        return cls(data=data, content=content, content_col=content_col, meta_col=meta_col)

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
            raise NotImplementedError("Data type not supported for metadata extraction.")


class Repo(BaseModel):

    # Name of this repo.
    name: str = Field(default="")
    docs: dict[Path, Document] = Field(default_factory=dict)
    codes: dict[Path, Document] = Field(default_factory=dict)
    assets: dict[Path, Document] = Field(default_factory=dict)
    repo_path: Path = Field(default_factory=Path)

    def _path(self, filename):
        return self.repo_path / filename

    @classmethod
    def from_path(cls, repo_path: Path):
        """Load documents, code, and assets from a repository path."""
        repo_path.mkdir(parents=True, exist_ok=True)
        repo = Repo(repo_path = repo_path)
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                repo._set(file_path.read_text(), file_path)
        return repo

    def to_path(self):
        """Persist all documents, code, and assets to the given repository path."""
        for doc in self.docs.values():
            doc.to_path()
        for code in self.codes.values():
            code.to_path()
        for asset in self.assets.values():
            asset.to_path()

    def _set(self, content: str, file_path: Path):
        """Add a document to the appropriate category based on its file extension."""
        file_ext = file_path.suffix

        doc = Document(content=content, file_path=file_path)
        if file_ext.lower() == '.md':
            self.docs[file_path] = doc
        elif file_ext.lower() in ['.py', '.js', '.css', '.html']:
            self.codes[file_path] = doc
        else:
            self.assets[file_path] = doc
        return doc

    def set(self, content: str, filename: str):
        """Set a document and persist it to disk."""
        file_path = self._path(filename)
        doc = self._set(content, file_path)
        doc.to_path()

    def get(self, filename: str) -> Optional[Document]:
        """Get a document by its filename."""
        path = self._path(filename)
        return self.docs.get(path) or self.codes.get(path) or self.assets.get(path)


def main():
    repo1 = Repo.from_path(Path("/Users/alexanderwu/workspace/t1"))
    repo1.set("wtf content", "doc/wtf_file.md")
    repo1.set("wtf code", "code/wtf_file.py")
    logger.info(repo1)  # check doc


if __name__ == '__main__':
    main()

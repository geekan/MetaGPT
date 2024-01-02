#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: File repository management. RFC 135 2.2.3.2, 2.2.3.4 and 2.2.3.13.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import aiofiles

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.schema import Document
from metagpt.utils.common import aread
from metagpt.utils.json_to_markdown import json_to_markdown


class FileRepository:
    """A class representing a FileRepository associated with a Git repository.

    :param git_repo: The associated GitRepository instance.
    :param relative_path: The relative path within the Git repository.

    Attributes:
        _relative_path (Path): The relative path within the Git repository.
        _git_repo (GitRepository): The associated GitRepository instance.
    """

    def __init__(self, git_repo, relative_path: Path = Path(".")):
        """Initialize a FileRepository instance.

        :param git_repo: The associated GitRepository instance.
        :param relative_path: The relative path within the Git repository.
        """
        self._relative_path = relative_path
        self._git_repo = git_repo

        # Initializing
        self.workdir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: Path | str, content, dependencies: List[str] = None):
        """Save content to a file and update its dependencies.

        :param filename: The filename or path within the repository.
        :param content: The content to be saved.
        :param dependencies: List of dependency filenames or paths.
        """
        pathname = self.workdir / filename
        pathname.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(str(pathname), mode="w") as writer:
            await writer.write(content)
        logger.info(f"save to: {str(pathname)}")

        if dependencies is not None:
            dependency_file = await self._git_repo.get_dependency()
            await dependency_file.update(pathname, set(dependencies))
            logger.info(f"update dependency: {str(pathname)}:{dependencies}")

    async def get_dependency(self, filename: Path | str) -> Set[str]:
        """Get the dependencies of a file.

        :param filename: The filename or path within the repository.
        :return: Set of dependency filenames or paths.
        """
        pathname = self.workdir / filename
        dependency_file = await self._git_repo.get_dependency()
        return await dependency_file.get(pathname)

    async def get_changed_dependency(self, filename: Path | str) -> Set[str]:
        """Get the dependencies of a file that have changed.

        :param filename: The filename or path within the repository.
        :return: List of changed dependency filenames or paths.
        """
        dependencies = await self.get_dependency(filename=filename)
        changed_files = set(self.changed_files.keys())
        changed_dependent_files = set()
        for df in dependencies:
            rdf = Path(df).relative_to(self._relative_path)
            if str(rdf) in changed_files:
                changed_dependent_files.add(df)
        return changed_dependent_files

    async def get(self, filename: Path | str) -> Document | None:
        """Read the content of a file.

        :param filename: The filename or path within the repository.
        :return: The content of the file.
        """
        doc = Document(root_path=str(self.root_path), filename=str(filename))
        path_name = self.workdir / filename
        if not path_name.exists():
            return None
        doc.content = await aread(path_name)
        return doc

    async def get_all(self) -> List[Document]:
        """Get the content of all files in the repository.

        :return: List of Document instances representing files.
        """
        docs = []
        for root, dirs, files in os.walk(str(self.workdir)):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.workdir)
                doc = await self.get(relative_path)
                docs.append(doc)
        return docs

    @property
    def workdir(self):
        """Return the absolute path to the working directory of the FileRepository.

        :return: The absolute path to the working directory.
        """
        return self._git_repo.workdir / self._relative_path

    @property
    def root_path(self):
        """Return the relative path from git repository root"""
        return self._relative_path

    @property
    def changed_files(self) -> Dict[str, str]:
        """Return a dictionary of changed files and their change types.

        :return: A dictionary where keys are file paths and values are change types.
        """
        files = self._git_repo.changed_files
        relative_files = {}
        for p, ct in files.items():
            if ct.value == "D":  # deleted
                continue
            try:
                rf = Path(p).relative_to(self._relative_path)
            except ValueError:
                continue
            relative_files[str(rf)] = ct
        return relative_files

    @property
    def all_files(self) -> List:
        """Get a dictionary of all files in the repository.

        The dictionary includes file paths relative to the current FileRepository.

        :return: A dictionary where keys are file paths and values are file information.
        :rtype: List
        """
        return self._git_repo.get_files(relative_path=self._relative_path)

    def get_change_dir_files(self, dir: Path | str) -> List:
        """Get the files in a directory that have changed.

        :param dir: The directory path within the repository.
        :return: List of changed filenames or paths within the directory.
        """
        changed_files = self.changed_files
        children = []
        for f in changed_files:
            try:
                Path(f).relative_to(Path(dir))
            except ValueError:
                continue
            children.append(str(f))
        return children

    @staticmethod
    def new_filename():
        """Generate a new filename based on the current timestamp and a UUID suffix.

        :return: A new filename string.
        """
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        return current_time
        # guid_suffix = str(uuid.uuid4())[:8]
        # return f"{current_time}x{guid_suffix}"

    async def save_doc(self, doc: Document, with_suffix: str = None, dependencies: List[str] = None):
        """Save a Document instance as a PDF file.

        This method converts the content of the Document instance to Markdown,
        saves it to a file with an optional specified suffix, and logs the saved file.

        :param doc: The Document instance to be saved.
        :type doc: Document
        :param with_suffix: An optional suffix to append to the saved file's name.
        :type with_suffix: str, optional
        :param dependencies: A list of dependencies for the saved file.
        :type dependencies: List[str], optional
        """
        m = json.loads(doc.content)
        filename = Path(doc.filename).with_suffix(with_suffix) if with_suffix is not None else Path(doc.filename)
        await self.save(filename=str(filename), content=json_to_markdown(m), dependencies=dependencies)
        logger.debug(f"File Saved: {str(filename)}")

    @staticmethod
    async def get_file(filename: Path | str, relative_path: Path | str = ".") -> Document | None:
        """Retrieve a specific file from the file repository.

        :param filename: The name or path of the file to retrieve.
        :type filename: Path or str
        :param relative_path: The relative path within the file repository.
        :type relative_path: Path or str, optional
        :return: The document representing the file, or None if not found.
        :rtype: Document or None
        """
        file_repo = CONFIG.git_repo.new_file_repository(relative_path=relative_path)
        return await file_repo.get(filename=filename)

    @staticmethod
    async def get_all_files(relative_path: Path | str = ".") -> List[Document]:
        """Retrieve all files from the file repository.

        :param relative_path: The relative path within the file repository.
        :type relative_path: Path or str, optional
        :return: A list of documents representing all files in the repository.
        :rtype: List[Document]
        """
        file_repo = CONFIG.git_repo.new_file_repository(relative_path=relative_path)
        return await file_repo.get_all()

    @staticmethod
    async def save_file(filename: Path | str, content, dependencies: List[str] = None, relative_path: Path | str = "."):
        """Save a file to the file repository.

        :param filename: The name or path of the file to save.
        :type filename: Path or str
        :param content: The content of the file.
        :param dependencies: A list of dependencies for the file.
        :type dependencies: List[str], optional
        :param relative_path: The relative path within the file repository.
        :type relative_path: Path or str, optional
        """
        file_repo = CONFIG.git_repo.new_file_repository(relative_path=relative_path)
        return await file_repo.save(filename=filename, content=content, dependencies=dependencies)

    @staticmethod
    async def save_as(
        doc: Document, with_suffix: str = None, dependencies: List[str] = None, relative_path: Path | str = "."
    ):
        """Save a Document instance with optional modifications.

        This static method creates a new FileRepository, saves the Document instance
        with optional modifications (such as a suffix), and logs the saved file.

        :param doc: The Document instance to be saved.
        :type doc: Document
        :param with_suffix: An optional suffix to append to the saved file's name.
        :type with_suffix: str, optional
        :param dependencies: A list of dependencies for the saved file.
        :type dependencies: List[str], optional
        :param relative_path: The relative path within the file repository.
        :type relative_path: Path or str, optional
        :return: A boolean indicating whether the save operation was successful.
        :rtype: bool
        """
        file_repo = CONFIG.git_repo.new_file_repository(relative_path=relative_path)
        return await file_repo.save_doc(doc=doc, with_suffix=with_suffix, dependencies=dependencies)

    async def delete(self, filename: Path | str):
        """Delete a file from the file repository.

        This method deletes a file from the file repository based on the provided filename.

        :param filename: The name or path of the file to be deleted.
        :type filename: Path or str
        """
        pathname = self.workdir / filename
        if not pathname.exists():
            return
        pathname.unlink(missing_ok=True)

        dependency_file = await self._git_repo.get_dependency()
        await dependency_file.update(filename=pathname, dependencies=None)
        logger.info(f"remove dependency key: {str(pathname)}")

    @staticmethod
    async def delete_file(filename: Path | str, relative_path: Path | str = "."):
        file_repo = CONFIG.git_repo.new_file_repository(relative_path=relative_path)
        await file_repo.delete(filename=filename)

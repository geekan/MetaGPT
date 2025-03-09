#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: Git repository management. RFC 135 2.2.3.3.
"""
from __future__ import annotations

import re
import shutil
import uuid
from enum import Enum
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Dict, List, Optional, Union
from urllib.parse import quote

from git.repo import Repo
from git.repo.fun import is_git_dir
from github import Auth, BadCredentialsException, Github
from github.GithubObject import NotSet
from github.Issue import Issue
from github.Label import Label
from github.Milestone import Milestone
from github.NamedUser import NamedUser
from github.PullRequest import PullRequest
from gitignore_parser import parse_gitignore
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.logs import logger
from metagpt.tools.libs.shell import shell_execute
from metagpt.utils.dependency_file import DependencyFile
from metagpt.utils.file_repository import FileRepository


class ChangeType(Enum):
    ADDED = "A"  # File was added
    COPIED = "C"  # File was copied
    DELETED = "D"  # File was deleted
    RENAMED = "R"  # File was renamed
    MODIFIED = "M"  # File was modified
    TYPE_CHANGED = "T"  # Type of the file was changed
    UNTRACTED = "U"  # File is untracked (not added to version control)


class RateLimitError(Exception):
    def __init__(self, message="Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class GitBranch(BaseModel):
    head: str
    base: str
    repo_name: str


class GitRepository:
    """A class representing a Git repository.

    :param local_path: The local path to the Git repository.
    :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.

    Attributes:
        _repository (Repo): The GitPython `Repo` object representing the Git repository.
    """

    def __init__(self, local_path=None, auto_init=True):
        """Initialize a GitRepository instance.

        :param local_path: The local path to the Git repository.
        :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.
        """
        self._repository = None
        self._dependency = None
        self._gitignore_rules = None
        if local_path:
            self.open(local_path=Path(local_path), auto_init=auto_init)

    def open(self, local_path: Path, auto_init=False):
        """Open an existing Git repository or initialize a new one if auto_init is True.

        :param local_path: The local path to the Git repository.
        :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.
        """
        local_path = Path(local_path)
        if self.is_git_dir(local_path):
            self._repository = Repo(local_path)
            self._gitignore_rules = parse_gitignore(full_path=str(local_path / ".gitignore"))
            return
        if not auto_init:
            return
        local_path.mkdir(parents=True, exist_ok=True)
        self._init(local_path)

    def _init(self, local_path: Path):
        """Initialize a new Git repository at the specified path.

        :param local_path: The local path where the new Git repository will be initialized.
        """
        self._repository = Repo.init(path=Path(local_path))

        gitignore_filename = Path(local_path) / ".gitignore"
        ignores = ["__pycache__", "*.pyc", ".vs"]
        with open(str(gitignore_filename), mode="w") as writer:
            writer.write("\n".join(ignores))
        self._repository.index.add([".gitignore"])
        self._repository.index.commit("Add .gitignore")
        self._gitignore_rules = parse_gitignore(full_path=gitignore_filename)

    def add_change(self, files: Dict):
        """Add or remove files from the staging area based on the provided changes.

        :param files: A dictionary where keys are file paths and values are instances of ChangeType.
        """
        if not self.is_valid or not files:
            return

        for k, v in files.items():
            self._repository.index.remove(k) if v is ChangeType.DELETED else self._repository.index.add([k])

    def commit(self, comments):
        """Commit the staged changes with the given comments.

        :param comments: Comments for the commit.
        """
        if self.is_valid:
            self._repository.index.commit(comments)

    def delete_repository(self):
        """Delete the entire repository directory."""
        if self.is_valid:
            try:
                shutil.rmtree(self._repository.working_dir)
            except Exception as e:
                logger.exception(f"Failed delete git repo:{self.workdir}, error:{e}")

    @property
    def changed_files(self) -> Dict[str, str]:
        """Return a dictionary of changed files and their change types.

        :return: A dictionary where keys are file paths and values are change types.
        """
        files = {i: ChangeType.UNTRACTED for i in self._repository.untracked_files}
        changed_files = {f.a_path: ChangeType(f.change_type) for f in self._repository.index.diff(None)}
        files.update(changed_files)
        return files

    @staticmethod
    def is_git_dir(local_path):
        """Check if the specified directory is a Git repository.

        :param local_path: The local path to check.
        :return: True if the directory is a Git repository, False otherwise.
        """
        if not local_path:
            return False
        git_dir = Path(local_path) / ".git"
        if git_dir.exists() and is_git_dir(git_dir):
            return True
        return False

    @property
    def is_valid(self):
        """Check if the Git repository is valid (exists and is initialized).

        :return: True if the repository is valid, False otherwise.
        """
        return bool(self._repository)

    @property
    def status(self) -> str:
        """Return the Git repository's status as a string."""
        if not self.is_valid:
            return ""
        return self._repository.git.status()

    @property
    def workdir(self) -> Path | None:
        """Return the path to the working directory of the Git repository.

        :return: The path to the working directory or None if the repository is not valid.
        """
        if not self.is_valid:
            return None
        return Path(self._repository.working_dir)

    @property
    def current_branch(self) -> str:
        """
        Returns the name of the current active branch.

        Returns:
            str: The name of the current active branch.
        """
        return self._repository.active_branch.name

    @property
    def remote_url(self) -> str:
        try:
            return self._repository.remotes.origin.url
        except AttributeError:
            return ""

    @property
    def repo_name(self) -> str:
        if self.remote_url:
            # This assumes a standard HTTPS or SSH format URL
            # HTTPS format example: https://github.com/username/repo_name.git
            # SSH format example: git@github.com:username/repo_name.git
            if self.remote_url.startswith("https://"):
                return self.remote_url.split("/", maxsplit=3)[-1].replace(".git", "")
            elif self.remote_url.startswith("git@"):
                return self.remote_url.split(":")[-1].replace(".git", "")
        return ""

    def new_branch(self, branch_name: str) -> str:
        """
        Creates a new branch with the given name.

        Args:
            branch_name (str): The name of the new branch to create.

        Returns:
            str: The name of the newly created branch.
                If the provided branch_name is empty, returns the name of the current active branch.
        """
        if not branch_name:
            return self.current_branch
        new_branch = self._repository.create_head(branch_name)
        new_branch.checkout()
        return new_branch.name

    def archive(self, comments="Archive"):
        """Archive the current state of the Git repository.

        :param comments: Comments for the archive commit.
        """
        logger.info(f"Archive: {list(self.changed_files.keys())}")
        if not self.changed_files:
            return
        self.add_change(self.changed_files)
        self.commit(comments)

    async def push(
        self, new_branch: str, comments="Archive", access_token: Optional[str] = None, auth: Optional[Auth] = None
    ) -> GitBranch:
        """
        Pushes changes to the remote repository.

        Args:
            new_branch (str): The name of the new branch to be pushed.
            comments (str, optional): Comments to be associated with the push. Defaults to "Archive".
            access_token (str, optional): Access token for authentication. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
            auth (Auth, optional): Optional authentication object. Defaults to None.

        Returns:
            GitBranch: The pushed branch object.

        Raises:
            ValueError: If neither `auth` nor `access_token` is provided.
            BadCredentialsException: If authentication fails due to bad credentials or timeout.

        Note:
            This function assumes that `self.current_branch`, `self.new_branch()`, `self.archive()`,
            `ctx.config.proxy`, `ctx.config`, `self.remote_url`, `shell_execute()`, and `logger` are
            defined and accessible within the scope of this function.
        """
        if not auth and not access_token:
            raise ValueError('`access_token` is invalid. Visit: "https://github.com/settings/tokens"')
        from metagpt.context import Context

        base = self.current_branch
        head = base if not new_branch else self.new_branch(new_branch)
        self.archive(comments)  # will skip committing if no changes
        ctx = Context()
        env = ctx.new_environ()
        proxy = ["-c", f"http.proxy={ctx.config.proxy}"] if ctx.config.proxy else []
        token = access_token or auth.token
        remote_url = f"https://{token}@" + self.remote_url.removeprefix("https://")
        command = ["git"] + proxy + ["push", remote_url]
        logger.info(" ".join(command).replace(token, "<TOKEN>"))
        try:
            stdout, stderr, return_code = await shell_execute(
                command=command, cwd=str(self.workdir), env=env, timeout=15
            )
        except TimeoutExpired as e:
            info = str(e).replace(token, "<TOKEN>")
            raise BadCredentialsException(status=401, message=info)
        info = f"{stdout}\n{stderr}\nexit: {return_code}\n"
        info = info.replace(token, "<TOKEN>")
        print(info)

        return GitBranch(base=base, head=head, repo_name=self.repo_name)

    def new_file_repository(self, relative_path: Path | str = ".") -> FileRepository:
        """Create a new instance of FileRepository associated with this Git repository.

        :param relative_path: The relative path to the file repository within the Git repository.
        :return: A new instance of FileRepository.
        """
        path = Path(relative_path)
        try:
            path = path.relative_to(self.workdir)
        except ValueError:
            path = relative_path
        return FileRepository(git_repo=self, relative_path=Path(path))

    async def get_dependency(self) -> DependencyFile:
        """Get the dependency file associated with the Git repository.

        :return: An instance of DependencyFile.
        """
        if not self._dependency:
            self._dependency = DependencyFile(workdir=self.workdir)
        return self._dependency

    def rename_root(self, new_dir_name):
        """Rename the root directory of the Git repository.

        :param new_dir_name: The new name for the root directory.
        """
        if self.workdir.name == new_dir_name:
            return
        new_path = self.workdir.parent / new_dir_name
        if new_path.exists():
            logger.info(f"Delete directory {str(new_path)}")
            try:
                shutil.rmtree(new_path)
            except Exception as e:
                logger.warning(f"rm {str(new_path)} error: {e}")
        if new_path.exists():  # Recheck for windows os
            logger.warning(f"Failed to delete directory {str(new_path)}")
            return
        try:
            shutil.move(src=str(self.workdir), dst=str(new_path))
        except Exception as e:
            logger.warning(f"Move {str(self.workdir)} to {str(new_path)} error: {e}")
        finally:
            if not new_path.exists():  # Recheck for windows os
                logger.warning(f"Failed to move {str(self.workdir)} to {str(new_path)}")
                return
        logger.info(f"Rename directory {str(self.workdir)} to {str(new_path)}")
        self._repository = Repo(new_path)
        self._gitignore_rules = parse_gitignore(full_path=str(new_path / ".gitignore"))

    def get_files(self, relative_path: Path | str, root_relative_path: Path | str = None, filter_ignored=True) -> List:
        """
        Retrieve a list of files in the specified relative path.

        The method returns a list of file paths relative to the current FileRepository.

        :param relative_path: The relative path within the repository.
        :type relative_path: Path or str
        :param root_relative_path: The root relative path within the repository.
        :type root_relative_path: Path or str
        :param filter_ignored: Flag to indicate whether to filter files based on .gitignore rules.
        :type filter_ignored: bool
        :return: A list of file paths in the specified directory.
        :rtype: List[str]
        """
        try:
            relative_path = Path(relative_path).relative_to(self.workdir)
        except ValueError:
            relative_path = Path(relative_path)

        if not root_relative_path:
            root_relative_path = Path(self.workdir) / relative_path
        files = []
        try:
            directory_path = Path(self.workdir) / relative_path
            if not directory_path.exists():
                return []
            for file_path in directory_path.iterdir():
                if not file_path.is_relative_to(root_relative_path):
                    continue
                if file_path.is_file():
                    rpath = file_path.relative_to(root_relative_path)
                    files.append(str(rpath))
                else:
                    subfolder_files = self.get_files(
                        relative_path=file_path, root_relative_path=root_relative_path, filter_ignored=False
                    )
                    files.extend(subfolder_files)
        except Exception as e:
            logger.error(f"Error: {e}")
        if not filter_ignored:
            return files
        filtered_files = self.filter_gitignore(filenames=files, root_relative_path=root_relative_path)
        return filtered_files

    def filter_gitignore(self, filenames: List[str], root_relative_path: Path | str = None) -> List[str]:
        """
        Filter a list of filenames based on .gitignore rules.

        :param filenames: A list of filenames to be filtered.
        :type filenames: List[str]
        :param root_relative_path: The root relative path within the repository.
        :type root_relative_path: Path or str
        :return: A list of filenames that pass the .gitignore filtering.
        :rtype: List[str]
        """
        if root_relative_path is None:
            root_relative_path = self.workdir
        files = []
        for filename in filenames:
            pathname = root_relative_path / filename
            if self._gitignore_rules(str(pathname)):
                continue
            files.append(filename)
        return files

    @classmethod
    @retry(wait=wait_random_exponential(min=1, max=15), stop=stop_after_attempt(3))
    async def clone_from(cls, url: str | Path, output_dir: str | Path = None) -> "GitRepository":
        from metagpt.context import Context

        to_path = Path(output_dir or Path(__file__).parent / f"../../workspace/downloads/{uuid.uuid4().hex}").resolve()
        to_path.mkdir(parents=True, exist_ok=True)
        repo_dir = to_path / Path(url).stem
        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)
        ctx = Context()
        env = ctx.new_environ()
        proxy = ["-c", f"http.proxy={ctx.config.proxy}"] if ctx.config.proxy else []
        command = ["git", "clone"] + proxy + [str(url)]
        logger.info(" ".join(command))

        stdout, stderr, return_code = await shell_execute(command=command, cwd=str(to_path), env=env, timeout=600)
        info = f"{stdout}\n{stderr}\nexit: {return_code}\n"
        logger.info(info)
        dir_name = Path(url).stem
        to_path = to_path / dir_name
        if not cls.is_git_dir(to_path):
            raise ValueError(info)
        logger.info(f"git clone to {to_path}")
        return GitRepository(local_path=to_path, auto_init=False)

    async def checkout(self, commit_id: str):
        self._repository.git.checkout(commit_id)
        logger.info(f"git checkout {commit_id}")

    def log(self) -> str:
        """Return git log"""
        return self._repository.git.log()

    @staticmethod
    async def create_pull(
        base: str,
        head: str,
        base_repo_name: str,
        head_repo_name: Optional[str] = None,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
        maintainer_can_modify: Optional[bool] = None,
        draft: Optional[bool] = None,
        issue: Optional[Issue] = None,
        access_token: Optional[str] = None,
        auth: Optional[Auth] = None,
    ) -> Union[PullRequest, str]:
        """
        Creates a pull request in the specified repository.

        Args:
            base (str): The name of the base branch.
            head (str): The name of the head branch.
            base_repo_name (str): The full repository name (user/repo) where the pull request will be created.
            head_repo_name (Optional[str], optional): The full repository name (user/repo) where the pull request will merge from. Defaults to None.
            title (Optional[str], optional): The title of the pull request. Defaults to None.
            body (Optional[str], optional): The body of the pull request. Defaults to None.
            maintainer_can_modify (Optional[bool], optional): Whether maintainers can modify the pull request. Defaults to None.
            draft (Optional[bool], optional): Whether the pull request is a draft. Defaults to None.
            issue (Optional[Issue], optional): The issue linked to the pull request. Defaults to None.
            access_token (Optional[str], optional): The access token for authentication. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
            auth (Optional[Auth], optional): The authentication method. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`

        Returns:
            PullRequest: The created pull request object.
        """
        title = title or NotSet
        body = body or NotSet
        maintainer_can_modify = maintainer_can_modify or NotSet
        draft = draft or NotSet
        issue = issue or NotSet
        if not auth and not access_token:
            raise ValueError('`access_token` is invalid. Visit: "https://github.com/settings/tokens"')
        clone_url = f"https://github.com/{base_repo_name}.git"
        try:
            auth = auth or Auth.Token(access_token)
            g = Github(auth=auth)
            base_repo = g.get_repo(base_repo_name)
            clone_url = base_repo.clone_url
            head_repo = g.get_repo(head_repo_name) if head_repo_name and head_repo_name != base_repo_name else None
            if head_repo:
                user = head_repo.full_name.split("/")[0]
                head = f"{user}:{head}"
            pr = base_repo.create_pull(
                base=base,
                head=head,
                title=title,
                body=body,
                maintainer_can_modify=maintainer_can_modify,
                draft=draft,
                issue=issue,
            )
        except Exception as e:
            logger.warning(f"Pull Request Error: {e}")
            return GitRepository.create_github_pull_url(
                clone_url=clone_url,
                base=base,
                head=head,
                head_repo_name=head_repo_name,
            )
        return pr

    @staticmethod
    async def create_issue(
        repo_name: str,
        title: str,
        body: Optional[str] = None,
        assignee: NamedUser | Optional[str] = None,
        milestone: Optional[Milestone] = None,
        labels: list[Label] | Optional[list[str]] = None,
        assignees: Optional[list[str]] | list[NamedUser] = None,
        access_token: Optional[str] = None,
        auth: Optional[Auth] = None,
    ) -> Issue:
        """
        Creates an issue in the specified repository.

        Args:
            repo_name (str): The full repository name (user/repo) where the issue will be created.
            title (str): The title of the issue.
            body (Optional[str], optional): The body of the issue. Defaults to None.
            assignee (Union[NamedUser, str], optional): The assignee for the issue, either as a NamedUser object or their username. Defaults to None.
            milestone (Optional[Milestone], optional): The milestone to associate with the issue. Defaults to None.
            labels (Union[list[Label], list[str]], optional): The labels to associate with the issue, either as Label objects or their names. Defaults to None.
            assignees (Union[list[str], list[NamedUser]], optional): The list of usernames or NamedUser objects to assign to the issue. Defaults to None.
            access_token (Optional[str], optional): The access token for authentication. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
            auth (Optional[Auth], optional): The authentication method. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`

        Returns:
            Issue: The created issue object.
        """
        body = body or NotSet
        assignee = assignee or NotSet
        milestone = milestone or NotSet
        labels = labels or NotSet
        assignees = assignees or NotSet
        if not auth and not access_token:
            raise ValueError('`access_token` is invalid. Visit: "https://github.com/settings/tokens"')
        auth = auth or Auth.Token(access_token)
        g = Github(auth=auth)

        repo = g.get_repo(repo_name)
        x_ratelimit_remaining = repo.raw_headers.get("x-ratelimit-remaining")
        if (
            x_ratelimit_remaining
            and bool(re.match(r"^-?\d+$", x_ratelimit_remaining))
            and int(x_ratelimit_remaining) <= 0
        ):
            raise RateLimitError()
        issue = repo.create_issue(
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
        )
        return issue

    @staticmethod
    async def get_repos(access_token: Optional[str] = None, auth: Optional[Auth] = None) -> List[str]:
        """
        Fetches a list of public repositories belonging to the authenticated user.

        Args:
            access_token (Optional[str], optional): The access token for authentication. Defaults to None.
                Visit `https://github.com/settings/tokens` for obtaining a personal access token.
            auth (Optional[Auth], optional): The authentication method. Defaults to None.
                Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html` for more information.

        Returns:
            List[str]: A list of full names of the public repositories belonging to the user.
        """
        auth = auth or Auth.Token(access_token)
        git = Github(auth=auth)
        user = git.get_user()
        v = user.get_repos(visibility="public")
        return [i.full_name for i in v]

    @staticmethod
    def create_github_pull_url(clone_url: str, base: str, head: str, head_repo_name: Optional[str] = None) -> str:
        """
        Create a URL for comparing changes between branches or repositories on GitHub.

        Args:
            clone_url (str): The URL used for cloning the repository, ending with '.git'.
            base (str): The base branch or commit.
            head (str): The head branch or commit.
            head_repo_name (str, optional): The name of the repository for the head branch. If not provided, assumes the same repository.

        Returns:
            str: The URL for comparing changes between the specified branches or commits.
        """
        url = clone_url.removesuffix(".git") + f"/compare/{base}..."
        if head_repo_name:
            url += head_repo_name.replace("/", ":")
        url += ":" + head
        return url

    @staticmethod
    def create_gitlab_merge_request_url(clone_url: str, head: str) -> str:
        """
        Create a URL for creating a new merge request on GitLab.

        Args:
            clone_url (str): The URL used for cloning the repository, ending with '.git'.
            head (str): The name of the branch to be merged.

        Returns:
            str: The URL for creating a new merge request for the specified branch.
        """
        return (
            clone_url.removesuffix(".git")
            + "/-/merge_requests/new?merge_request%5Bsource_branch%5D="
            + quote(head, safe="")
        )

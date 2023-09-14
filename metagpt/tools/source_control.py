

import os
from git import Repo, Actor
from pathlib import PosixPath

class GitControl:
    def __init__(self, workspace: str | PosixPath) -> None:
        self.workspace = workspace
        try:
            repo = Repo(workspace)
            self.git_repo = repo.index
        except:
            self.init()

    def init(self):
        repo = Repo.init(self.workspace)
        self.git_repo = repo.index

    def add(self, file: str | PosixPath | list[str] | list[PosixPath]):
        self.git_repo.add(file)

    def commit(self, commit: str, author: dict, committer: dict | None = None):
        self.author = Actor(author["name"], author["email"])
        if(committer):
            self.committer = Actor(committer['name'], committer['email'])
        else:
            self.committer = None
        self.git_repo.commit(commit, author=self.author, committer=self.committer)

    def add_and_commit(self, workspace: str | PosixPath,  file: list[str] | list[PosixPath],
                       author: dict, committer: dict | None = None):
        files_exists = [ f for f in file if os.path.exists(f)]
        self.add(files_exists)
        commit = f"{author['name']}({author['email']}) add files:"
        for f in files_exists:
            commit += " " + str(f).split(str(workspace))[1]
        self.commit(commit, author=author, committer=committer)

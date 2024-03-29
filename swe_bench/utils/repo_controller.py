from pathlib import Path
from typing import Optional

import git

from metagpt.logs import logger


class RepoController:
    def __init__(self, user_name: str, repo_name: str, root_dir: Path, remote_url: Optional[str] = None):
        self.user_name = user_name
        self.repo_name = repo_name
        self.local_path = root_dir / user_name / repo_name
        if remote_url is None:
            self.remote_url = "https://github.com/"
        self._repo: Optional[git.Repo] = None

    @property
    def repo(self) -> git.Repo:
        if self._repo is None:
            if not Path.exists(self.local_path):
                self.git_clone()
            self._repo = git.Repo(self.local_path)
        return self._repo

    def git_clone(self):
        repo_url = self.remote_url + f"{self.user_name}/{self.repo_name}.git"
        git.Repo.clone_from(repo_url, self.local_path)

    def checkout_commit(self, commit_hash):
        try:
            self.repo.git.checkout(commit_hash)
        except Exception as e:
            logger.warning(f"Failed to checkout commit {commit_hash}: {e}")


def init_repo(swe_row):
    repo_user_name, repo_name = swe_row["repo"].split("/")
    base_commit = swe_row["base_commit"]
    current_path = Path.cwd()
    repo_path = current_path / "repo"
    logger.debug(f"repo: {swe_row['repo']}, commit: {swe_row['base_commit']}")
    logger.debug(f"instance: {swe_row['instance_id']}")

    repo_controller = RepoController(repo_user_name, repo_name, repo_path)
    repo_controller.checkout_commit(base_commit)
    return repo_controller

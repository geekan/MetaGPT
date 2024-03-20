import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import git
from git.exc import GitError

from metagpt.logs import logger
from metagpt.utils.exceptions import handle_exception

KEY_INSTANCE_ID = "instance_id"
RESET_FAILED = ">>>>> Reset Failed"


class ExecWrapper:
    def __init__(self, subprocess_args: Dict = None):
        self.subprocess_args = subprocess_args or {}

    @handle_exception(exception_type=subprocess.CalledProcessError)
    def __call__(self, cmd, raise_error=True, **kwargs):
        combined_args = {**self.subprocess_args, **kwargs}
        output = subprocess.run(cmd, **combined_args)
        return output


class EnvManager:
    def __init__(self, testbed):
        shellenv = os.environ.copy()
        self.testbed = testbed

        self.exec = ExecWrapper(
            subprocess_args={
                "check": True,
                "shell": False,
                "capture_output": True,
                "text": True,
                "env": shellenv,
            }
        )

    @handle_exception(exception_type=GitError)
    def clone_repo(self, repo_name: str, path: str, token: str = None):
        if token is None:
            token = os.environ.get("GITHUB_TOKEN", "git")
            if not token:
                raise ValueError("GitHub token is required for cloning repositories.")

        repo_url = f"https://{token}@github.com/swe-bench/{repo_name.replace('/', '__')}.git"
        os.makedirs(path, exist_ok=True)

        # Clone the repository
        git.Repo.clone_from(repo_url, path)
        logger.info(f"Repository '{repo_name}' cloned successfully.")

    @handle_exception(exception_type=Exception)  # Using a broad exception type for the example
    def copy_repo(self, source_path: str, destination_path: str):
        if not os.path.isdir(source_path):
            raise ValueError("Source path does not exist or is not a directory.")

        os.makedirs(destination_path, exist_ok=True)

        # Copy the repository
        try:
            shutil.copytree(
                source_path, destination_path, dirs_exist_ok=True
            )  # For Python 3.8+, dirs_exist_ok handles existing directories
        except TypeError:
            # Fallback for Python < 3.8, where dirs_exist_ok is not available
            if os.listdir(destination_path):  # If destination is not empty
                raise ValueError("Destination directory is not empty and dirs_exist_ok is not supported.")
            shutil.copytree(source_path, destination_path)

        logger.info(f"Repository contents from '{source_path}' copied successfully to '{destination_path}'.")

    @handle_exception(exception_type=Exception, default_return=False)
    def reset_task_env(self, instance: Dict):
        """
        Reset task environment + testbed and checkout base commit of given task instance
        """
        gitignore_path = Path(".gitignore")
        if gitignore_path.exists():
            self.exec(["git", "ls-files", "--ignored", "--exclude-standard", "-o", "-z"], raise_error=False)
            # fixme: need detect platform and change this cmd
            # self.exec(["xargs", "-0", "-r", "rm", "-rf"], input=gitignore_path.read_text())

        self.exec(["git", "restore", "."])
        self.exec(["git", "reset", "HEAD", "."])
        self.exec(["git", "clean", "-fdx"])
        self.exec(["git", "-c", "advice.detachedHead=false", "checkout", instance["base_commit"]])
        logger.info(f"[{instance['instance_id']}] Reset task environment to {instance['base_commit']}")
        return True

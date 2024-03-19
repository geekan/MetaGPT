import os
import subprocess
from pathlib import Path
from traceback import format_exc
from typing import Dict

import git
from git.exc import GitError

from metagpt.logs import logger

KEY_INSTANCE_ID = "instance_id"
RESET_FAILED = ">>>>> Reset Failed"


class ExecWrapper:
    def __init__(self, subprocess_args: Dict = None):
        self.subprocess_args = subprocess_args or {}

    def __call__(self, cmd, raise_error=True, **kwargs):
        try:
            combined_args = {**self.subprocess_args, **kwargs}
            output = subprocess.run(cmd, **combined_args)
            return output
        except subprocess.CalledProcessError as e:
            if raise_error:
                error_message = (
                    f"Error: {e}\nError stdout: {e.stdout}\nError stderr: {e.stderr}\nError traceback: {format_exc()}"
                )
                logger.error(error_message)
                raise e


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

    def clone_repo(self, repo_name: str, path: str, token: str = None):
        if token is None:
            token = os.environ.get("GITHUB_TOKEN", "git")
            if not token:
                raise ValueError("GitHub token is required for cloning repositories.")

        repo_url = f"https://{token}@github.com/swe-bench/{repo_name.replace('/', '__')}.git"

        try:
            # Ensure the destination directory exists
            os.makedirs(path, exist_ok=True)

            # Clone the repository
            git.Repo.clone_from(repo_url, path)
            print(f"Repository '{repo_name}' cloned successfully.")
        except GitError as e:
            print(f"Failed to clone repository '{repo_name}': {e}")

    def reset_task_env(self, instance: Dict):
        """
        Reset task environment + testbed and checkout base commit of given task instance
        """
        try:
            gitignore_path = Path(".gitignore")
            if gitignore_path.exists():
                self.exec(["git", "ls-files", "--ignored", "--exclude-standard", "-o", "-z"], raise_error=False)
                # self.exec(["xargs", "-0", "-r", "rm", "-rf"], input=gitignore_path.read_text())

            self.exec(["git", "restore", "."])
            self.exec(["git", "reset", "HEAD", "."])
            self.exec(["git", "clean", "-fdx"])
            self.exec(["git", "-c", "advice.detachedHead=false", "checkout", instance["base_commit"]])
            logger.info(f"[{instance['instance_id']}] Reset task environment to {instance['base_commit']}")
            return True
        except Exception as e:
            err_msg = f"{RESET_FAILED}; Failed to reset task environment to {instance['base_commit']}: {e}"
            logger.error(err_msg)
            return False

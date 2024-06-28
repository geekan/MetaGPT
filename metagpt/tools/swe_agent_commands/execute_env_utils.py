import json
import os
import re
import select
import shlex
import subprocess
import tarfile
import tempfile
import threading
import time
import traceback
from io import BytesIO
from subprocess import PIPE, STDOUT
from typing import Tuple

import docker
from datasets import load_dataset, load_from_disk
from ghapi.all import GhApi

from metagpt.logs import logger

LOGGER_NAME = "intercode"
START_UP_DELAY = 5
TIMEOUT_DURATION = 25
GITHUB_ISSUE_URL_PATTERN = re.compile(r"github\.com\/(.*?)\/(.*?)\/issues\/(\d+)")


def is_from_github_url(data_path: str):
    return GITHUB_ISSUE_URL_PATTERN.search(data_path) is not None


def copy_file_to_container(container, contents, container_path):
    """
    Copies a given string into a Docker container at a specified path.

    Args:
    - container: Docker SDK container object.
    - contents: The string to copy into the container.
    - container_path: The path inside the container where the string should be copied to.

    Returns:
    - None
    """
    temp_file_name = None

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name
            # Write the string to the temporary file and ensure it's written to disk
            temp_file.write(contents.encode("utf-8"))
            temp_file.flush()
            os.fsync(temp_file.fileno())

        # Create a TAR archive in memory containing the temporary file
        with tempfile.NamedTemporaryFile():
            with open(temp_file_name, "rb") as temp_file:
                # Prepare the TAR archive
                with BytesIO() as tar_stream:
                    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                        tar_info = tarfile.TarInfo(name=os.path.basename(container_path))
                        tar_info.size = os.path.getsize(temp_file_name)
                        tar.addfile(tarinfo=tar_info, fileobj=temp_file)
                    tar_stream.seek(0)
                    # Copy the TAR stream to the container
                    container.put_archive(path=os.path.dirname(container_path), data=tar_stream.read())

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Cleanup: Remove the temporary file if it was created
        if temp_file_name and os.path.exists(temp_file_name):
            os.remove(temp_file_name)


def read_with_timeout(container, pid_func, timeout_duration):
    """
    Read data from a subprocess with a timeout.
    This function uses a file descriptor to read data from the subprocess in a non-blocking way.

    Args:
        container (subprocess.Popen): The subprocess container.
        pid_func (function): A function that returns a list of process IDs (except the PID of the main process).
        timeout_duration (int): The timeout duration in seconds.

    Returns:
        str: The data read from the subprocess, stripped of trailing newline characters.

    Raises:
        TimeoutError: If the timeout duration is reached while reading from the subprocess.
    """
    buffer = b""
    fd = container.stdout.fileno()
    end_time = time.time() + timeout_duration

    while time.time() < end_time:
        pids = pid_func()
        if len(pids) > 0:
            # There are still PIDs running
            time.sleep(0.05)
            continue
        ready_to_read, _, _ = select.select([fd], [], [], 0.1)
        if ready_to_read:
            data = os.read(fd, 4096)
            if data:
                buffer += data
        else:
            # No more data to read
            break
        time.sleep(0.05)  # Prevents CPU hogging

    if container.poll() is not None:
        raise RuntimeError("Subprocess exited unexpectedly.\nCurrent buffer: {}".format(buffer.decode()))
    if time.time() >= end_time:
        raise TimeoutError(
            "Timeout reached while reading from subprocess.\nCurrent buffer: {}\nRunning PIDs: {}".format(
                buffer.decode(), pids
            )
        )
    return buffer.decode()


class timeout:
    def __init__(self, seconds=TIMEOUT_DURATION, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message
        self.timer = None
        self.timeout_occurred = False

    def handle_timeout(self, signum=None, frame=None):
        self.timeout_occurred = True

    def __enter__(self):
        # signal.signal(signal.SIGALRM, self.handle_timeout)
        # signal.alarm(self.seconds)
        self.timer = threading.Timer(self.seconds, self.handle_timeout)
        self.timer.start()
        return self

    def __exit__(self, type, value, traceback):
        self.timer.cancel()
        if self.timeout_occurred:
            print(self.error_message)  # 处理超时的逻辑


def get_background_pids(container_obj):
    pids = container_obj.exec_run("ps -eo pid,comm --no-headers").output.decode().split("\n")
    pids = [x.split() for x in pids if x]
    pids = [x for x in pids if x[1] not in {"ps"} and x[0] != "1"]
    bash_pids = [x for x in pids if x[1] == "bash"]
    other_pids = [x for x in pids if x[1] not in {"bash"}]
    return bash_pids, other_pids


def _get_non_persistent_container(ctr_name: str, image_name: str) -> Tuple[subprocess.Popen, set]:
    startup_cmd = [
        "docker",
        "run",
        "-i",
        "--rm",
        "--name",
        ctr_name,
        image_name,
        "/bin/bash",
        "-l",
        "-m",
    ]

    logger.debug("Starting container with command: %s", shlex.join(startup_cmd))
    container = subprocess.Popen(
        startup_cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,  # line buffered
    )
    time.sleep(START_UP_DELAY)
    # try to read output from container setup (usually an error), timeout if no output
    try:
        with timeout(seconds=2):
            output = container.stdout.read()
            if output:
                logger.error(f"Unexpected container setup output: {output}")
    except TimeoutError:
        pass
    return container, {
        "1",
    }  # bash PID is always 1 for non-persistent containers


def _get_persistent_container(ctr_name: str, image_name: str, persistent: bool = False) -> Tuple[subprocess.Popen, set]:
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"name": ctr_name})
    if ctr_name in [c.name for c in containers]:
        container_obj = client.containers.get(ctr_name)
        if container_obj.status in {"created"}:
            container_obj.start()
        elif container_obj.status in {"running"}:
            pass
        elif container_obj.status in {"exited"}:
            container_obj.restart()
        elif container_obj.status in {"paused"}:
            container_obj.unpause()
        else:
            raise RuntimeError(f"Unexpected container status: {container_obj.status}")
    else:
        container_obj = client.containers.run(
            image_name,
            command="/bin/bash -l -m",
            name=ctr_name,
            stdin_open=True,
            tty=True,
            detach=True,
            auto_remove=not persistent,
        )
        container_obj.start()
    startup_cmd = [
        "docker",
        "exec",
        "-i",
        ctr_name,
        "/bin/bash",
        "-l",
        "-m",
    ]
    logger.debug("Starting container with command: %s", shlex.join(startup_cmd))
    container = subprocess.Popen(
        startup_cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,  # line buffered
    )
    time.sleep(START_UP_DELAY)
    # try to read output from container setup (usually an error), timeout if no output
    try:
        with timeout(seconds=2):
            output = container.stdout.read()
            if output:
                logger.error(f"Unexpected container setup output: {output}")
    except TimeoutError:
        pass
    # Get the process IDs of the container
    # There should be at least a head process and possibly one child bash process
    bash_pids, other_pids = get_background_pids(container_obj)
    bash_pid = 1
    if len(bash_pids) == 1:
        bash_pid = bash_pids[0][0]
    elif len(bash_pids) > 1 or len(other_pids) > 0:
        raise RuntimeError(
            f"Detected alien processes attached or running. Please ensure that no other agents are running on this container. PIDs: {bash_pids}, {other_pids}"
        )
    return container, set(
        map(
            str,
            [
                bash_pid,
                1,
            ],
        )
    )


def get_container(ctr_name: str, image_name: str, persistent: bool = False) -> subprocess.Popen:
    """
    Get a container object for a given container name and image name

    Arguments:
        ctr_name (str): Name of container
        image_name (str): Name of image
        persistent (bool): Whether to use a persistent container or not
    Returns:
        Container object
    """
    if persistent:
        return _get_persistent_container(ctr_name, image_name)
    else:
        return _get_non_persistent_container(ctr_name, image_name)


def get_commit(api: GhApi, owner: str, repo: str, base_commit: str = None):
    if base_commit:
        commit = api.repos.get_commit(owner, repo, base_commit)
    else:
        commit = api.repos.list_commits(owner, repo)[0]
    return commit


class InvalidGithubURL(ValueError):
    ...


def parse_gh_issue_url(issue_url: str) -> Tuple[str, str, str]:
    """Return owner, repo, issue number from issue url"""
    match = GITHUB_ISSUE_URL_PATTERN.search(issue_url)
    if not match:
        raise InvalidGithubURL(f"Invalid GitHub issue URL: {issue_url}")
    res = match.groups()
    assert len(res) == 3
    return tuple(res)  # type: ignore


def get_instances(file_path: str, base_commit: str = None, split: str = None, token: str = None):
    """
    Getter function for handling json, jsonl files

    Arguments:
        file_path (str): Path to file
    Returns:
        List of instances
    """
    # If file_path is a directory, attempt load from disk
    if os.path.isdir(file_path):
        dataset_or_dict = load_from_disk(file_path)
        if isinstance(dataset_or_dict, dict):
            return dataset_or_dict[split]
        return dataset_or_dict

    # If file_path is a github issue url, fetch the issue and return a single instance
    if is_from_github_url(file_path):
        try:
            owner, repo, issue_number = parse_gh_issue_url(file_path)
        except InvalidGithubURL:
            pass
        else:
            record = dict()
            api = GhApi(token=token)
            issue = api.issues.get(owner, repo, issue_number)
            title = issue.title if issue.title else ""
            body = issue.body if issue.body else ""
            text = f"{title}\n{body}\n"
            record["repo"] = f"{owner}/{repo}"
            record["base_commit"] = base_commit if base_commit else get_commit(api, owner, repo, base_commit).sha
            record["version"] = record["base_commit"][:7]
            record["problem_statement"] = text
            record["instance_id"] = f"{owner}__{repo}-i{issue_number}"
            return [
                record,
            ]
    elif base_commit is not None:
        raise ValueError("base_commit must be None if data_path is not a github issue url")

    # If file_path is a file, load the file
    if file_path.endswith(".json"):
        return json.load(open(file_path))
    if file_path.endswith(".jsonl"):
        return [json.loads(x) for x in open(file_path, "r").readlines()]

    # Attempt load from HF datasets as a last resort
    try:
        return load_dataset(file_path, split=split)
    except:
        raise ValueError(
            f"Could not load instances from {file_path}. "
            "Please ensure --data_path is a GitHub URL, a SWE-bench HuggingFace dataset, or a JSON/JSONL file."
        )

# Import necessary libraries and modules
import gzip
import itertools
import json
import os
import subprocess
from typing import Dict, Iterable, List, Union

import numpy as np
import tqdm
from loguru import logger

# Define the root directory as the location of the script
ROOT = os.path.dirname(os.path.abspath(__file__))

# Define the input data file containing human evaluations
HUMAN_EVAL = r"HumanEval.jsonl.gz"


def read_problems(evalset_file: str = HUMAN_EVAL) -> Dict[str, Dict]:
    """
    Reads a JSONL file containing problem evaluations and returns them as a dictionary.

    Args:
        evalset_file (str): Path to the JSONL file.

    Returns:
        Dict[str, Dict]: A dictionary where task IDs are keys and problem details are values.
    """
    return {task["task_id"]: task for task in stream_jsonl(evalset_file)}


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses a JSONL file and yields each line as a dictionary.

    Args:
        filename (str): Path to the JSONL file.

    Yields:
        Iterable[Dict]: A generator of dictionaries representing JSONL lines.
    """
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt") as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def _generate_examples(filepath, split, name="sanitized"):
    if name == "full":

        def _read_lines(fn, start, end):
            data = []
            with open(fn, encoding="utf-8") as f:
                for line in f:
                    sample = json.loads(line)
                    if start <= sample["task_id"] <= end:
                        data.append(sample)
                    elif sample["task_id"] > end:
                        break
            return data

        if split == "test":
            data = _read_lines(filepath, 11, 510)
        elif split == "train":
            data = _read_lines(filepath, 601, 974)
        elif split == "validation":
            data = _read_lines(filepath, 511, 600)
        elif split == "prompt":
            data = _read_lines(filepath, 1, 10)

    elif name == "sanitized":
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        if split == "test":
            data = [sample for sample in data if 11 <= sample["task_id"] <= 510]
        elif split == "train":
            data = [sample for sample in data if 601 <= sample["task_id"] <= 974]
        elif split == "validation":
            data = [sample for sample in data if 511 <= sample["task_id"] <= 600]
        elif split == "prompt":
            data = [sample for sample in data if 1 <= sample["task_id"] <= 10]
    id_ = 0
    for sample in data:
        yield id_, sample
        id_ += 1


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to a JSONL file.

    Args:
        filename (str): Path to the output JSONL file.
        data (Iterable[Dict]): Data to write as JSONL.
        append (bool): If True, appends to an existing file, else creates a new file.
    """
    # Determine the file writing mode based on the 'append' flag
    if append:
        mode = "ab"
    else:
        mode = "wb"
    filename = os.path.expanduser(filename)

    # Handle .gz compression
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode="wb") as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode("utf-8"))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode("utf-8"))


def execution(task_id, check_program):
    """
    Executes a Python program and captures its output.

    Args:
        task_id: A unique identifier for the task.
        check_program: The Python program to execute.

    Returns:
        bool: True if the execution was successful, False otherwise.
    """
    process = subprocess.Popen(["python", "-c", f"{check_program}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Wait for the process to complete, with a timeout
        stdout, stderr = process.communicate(timeout=30)

        if len(stderr) == 0:
            # logger.info(f"{task_id}: passed")
            passed = True
        elif b"OK" in stderr:
            # logger.info(f"{task_id}: passed, {stderr}")
            passed = True

        else:
            logger.info(f"{task_id}: error: {stderr}")
            passed = False
    except subprocess.TimeoutExpired:
        logger.info("The command did not complete within the given timeout.")
        process.kill()  # Kill the process if it times out
        logger.info(f"{task_id}: error")
        passed = False
    return passed


def estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray], num_correct: Union[List[int], np.ndarray], k: int
) -> np.ndarray:
    """
    Estimates pass@k of each problem and returns them in an array.

    Args:
        num_samples: Number of total samples (can be an int, list, or NumPy array).
        num_correct: Number of correct samples (list or NumPy array).
        k (int): The 'k' value for pass@k.

    Returns:
        np.ndarray: An array of pass rates for each problem.
    """

    # Define a pass rate estimator function
    def estimator(n: int, c: int, k: int) -> float:
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    # Determine the number of samples based on the input type
    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    # Calculate pass rates for each problem
    return np.array([estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)])


def evaluate(total: List, correct: List, ks: List = [1, 10]):
    """
    Evaluates and logs pass rates at various 'k' values.

    Args:
        total (List): List of total samples.
        correct (List): List of correct samples.
        ks (List): List of 'k' values to evaluate.

    Returns:
        dict: A dictionary of pass rates at each 'k' value.
    """
    total = np.array(total)
    correct = np.array(correct)

    # Calculate and log pass rates at each 'k' value
    pass_at_k = {f"pass@{k}": estimate_pass_at_k(total, correct, k).mean() for k in ks if (total >= k).all()}
    logger.info(pass_at_k)
    return pass_at_k


if __name__ == "__main__":
    logger.info("Reading samples...")
    problems = read_problems(HUMAN_EVAL)

    total, correct = [], []
    passed = []

    for sample in tqdm.tqdm(stream_jsonl("example_samples.jsonl")):
        task_id = sample["task_id"]
        completion = sample["completion"]
        problem = problems[task_id]

        # Construct a check program
        check_program = completion + "\n" + problem["test"] + "\n" + f"check({problem['entry_point']})"

        # Execute the check program and capture the result
        passed_flg = execution(task_id, check_program)

        if not passed_flg:
            logger.debug("error")
        else:
            logger.debug("passed")
            passed.append(len(passed))

            total.append(len(passed))
            correct.append(sum(passed))

    # Evaluate pass rates at various 'k' values
    evaluate(total, correct, ks=[1, 5, 10])

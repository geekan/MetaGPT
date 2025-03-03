"""Load and save experiences from the log file."""

import json
from pathlib import Path

from metagpt.exp_pool import get_exp_manager
from metagpt.exp_pool.schema import LOG_NEW_EXPERIENCE_PREFIX, Experience
from metagpt.logs import logger


def load_exps(log_file_path: str) -> list[Experience]:
    """Loads experiences from a log file.

    Args:
        log_file_path (str): The path to the log file.

    Returns:
        list[Experience]: A list of Experience objects loaded from the log file.
    """

    if not Path(log_file_path).exists():
        logger.warning(f"`load_exps` called with a non-existent log file path: {log_file_path}")
        return

    exps = []
    with open(log_file_path, "r") as log_file:
        for line in log_file:
            if LOG_NEW_EXPERIENCE_PREFIX in line:
                json_str = line.split(LOG_NEW_EXPERIENCE_PREFIX, 1)[1].strip()
                exp_data = json.loads(json_str)

                exp = Experience(**exp_data)
                exps.append(exp)

    logger.info(f"Loaded {len(exps)} experiences from log file: {log_file_path}")

    return exps


def save_exps(exps: list[Experience]):
    """Saves a list of experiences to the experience pool.

    Args:
        exps (list[Experience]): The list of experiences to save.
    """

    if not exps:
        logger.warning("`save_exps` called with an empty list of experiences.")
        return

    manager = get_exp_manager()
    manager.is_writable = True

    manager.create_exps(exps)
    logger.info(f"Saved {len(exps)} experiences.")


def get_log_file_path() -> str:
    """Retrieves the path to the log file.

    Returns:
        str: The path to the log file.

    Raises:
        ValueError: If the log file path cannot be found.
    """

    handlers = logger._core.handlers

    for handler in handlers.values():
        if "log" in handler._name:
            return handler._name[1:-1]

    raise ValueError("Log file not found")


def main():
    log_file_path = get_log_file_path()

    exps = load_exps(log_file_path)
    save_exps(exps)


if __name__ == "__main__":
    main()

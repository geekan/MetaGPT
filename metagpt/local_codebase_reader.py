#import os, logging, pathlib
from typing import List, Optional

# Configuration for logging
logger = logging.getLogger('local_codebase_reader')
logger.setLevel(logging.INFO)

def read_local_codebase(directory: str, file_types: Optional[List[str]] = None) -> dict:
    """
    Reads files from the specified directory and returns their contents.
    This version allows for specifying different file types.
    Args:
    - directory (str): The path to the directory containing the codebase files.
    - file_types (Optional[List[str]]): List of file extensions to include. Defaults to None, which means all files are included.
    Returns:
    - dict: A dictionary with filenames as keys and file contents as values.
    """
    if not file_types:
        file_types = ['*'] # If none, include all files.

    files_content = {}
    try:
        for filename in os.listdir(directory):
            if any(filename.endswith(ft) for ft in file_types):
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r') as file:
                    files_content[filename] = file.read()
    except Exception as e:
        logger.error(f'Error reading files from {directory}: {e}')

    return files_content

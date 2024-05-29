import os
from dataclasses import dataclass
from typing import Optional

import yaml


# Copy from OpenDevin
@dataclass()
class Command:
    name: str
    docstring: Optional[str] = None
    signature: Optional[str] = None


def parse_command_file(filepath: str) -> str:
    content = open(filepath, "r").read()
    lines = content.split("\n")
    commands: list[Command] = []
    idx = 0
    docs: list[str] = []
    while idx < len(lines):
        line = lines[idx]
        idx += 1
        if line.startswith("# "):
            docs.append(line[2:])
        elif line.strip().endswith("() {"):
            name = line.split()[0][:-2]
            while lines[idx].strip() != "}":
                idx += 1
            docstring, signature = None, name
            docs_dict = yaml.safe_load("\n".join(docs).replace("@yaml", ""))
            if docs_dict is not None:
                docstring = docs_dict.get("docstring")
                arguments = docs_dict.get("arguments", None)
                if "signature" in docs_dict:
                    signature = docs_dict["signature"]
                else:
                    if arguments is not None:
                        for param, settings in arguments.items():
                            if "required" in settings:
                                signature += f" <{param}>"
                            else:
                                signature += f" [<{param}>]"
            command = Command(name, docstring, signature)
            commands.append(command)
            docs = []
    function_docs = ""
    for cmd in commands:
        if cmd.docstring is not None:
            function_docs += f"{cmd.signature or cmd.name} - {cmd.docstring}\n"
    return function_docs


def _resolve_to_cur_dir(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def check_and_parse_command_file(filepath) -> str:
    if filepath is None:
        raise FileNotFoundError(f"File not found: {filepath}")
    return parse_command_file(filepath)


DEFAULT_SCRIPT_FILEPATHS = [
    _resolve_to_cur_dir("defaults.sh"),
    _resolve_to_cur_dir("search.sh"),
    _resolve_to_cur_dir("edit_linting.sh"),
]
DEFAULT_DOCUMENTATION = "".join(
    [check_and_parse_command_file(filepath) for filepath in DEFAULT_SCRIPT_FILEPATHS if filepath is not None]
)

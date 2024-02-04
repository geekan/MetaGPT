import re
from typing import Tuple

from pydantic import BaseModel


def remove_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


class DocstringParser(BaseModel):
    docstring: str

    def parse_desc(self) -> str:
        """Parse and return the description from the docstring."""

    def parse_params(self) -> list[Tuple[str, str, str]]:
        """Parse and return the parameters from the docstring.

        Returns:
            list[Tuple[str, str, str]]: A list of input paramter info. Each info is a triple of (param name, param type, param description)
        """

    def parse_returns(self) -> list[Tuple[str, str]]:
        """Parse and return the output information from the docstring.

        Returns:
            list[Tuple[str, str]]: A list of output info. Each info is a tuple of (return type, return description)
        """

    @staticmethod
    def check_and_parse_optional(param_type: str) -> Tuple[bool, str]:
        """Check if a parameter is optional and return a processed param_type rid of the optionality info if so"""

    @staticmethod
    def check_and_parse_default_value(param_desc: str) -> Tuple[bool, str]:
        """Check if a parameter has a default value and return the default value if so"""

    @staticmethod
    def check_and_parse_enum(param_desc: str) -> Tuple[bool, str]:
        """Check if a parameter description includes an enum and return enum values if so"""


class reSTDocstringParser(DocstringParser):
    """A parser for reStructuredText (reST) docstring"""


class GoogleDocstringParser(DocstringParser):
    """A parser for Google-stype docstring"""

    docstring: str

    def parse_desc(self) -> str:
        description_match = re.search(r"^(.*?)(?:Args:|Returns:|Raises:|$)", self.docstring, re.DOTALL)
        description = remove_spaces(description_match.group(1)) if description_match else ""
        return description

    def parse_params(self) -> list[Tuple[str, str, str]]:
        args_match = re.search(r"Args:\s*(.*?)(?:Returns:|Raises:|$)", self.docstring, re.DOTALL)
        _args = args_match.group(1).strip() if args_match else ""
        # variable_pattern = re.compile(r"(\w+)\s*\((.*?)\):\s*(.*)")
        variable_pattern = re.compile(
            r"(\w+)\s*\((.*?)\):\s*(.*?)(?=\n\s*\w+\s*\(|\Z)", re.DOTALL
        )  # (?=\n\w+\s*\(|\Z) is to assert that what follows is either the start of the next parameter (indicated by a newline, some word characters, and an opening parenthesis) or the end of the string (\Z).
        params = variable_pattern.findall(_args)
        return params

    def parse_returns(self) -> list[Tuple[str, str]]:
        returns_match = re.search(r"Returns:\s*(.*?)(?:Raises:|$)", self.docstring, re.DOTALL)
        returns = returns_match.group(1).strip() if returns_match else ""
        return_pattern = re.compile(r"^(.*)\s*:\s*(.*)$")
        returns = return_pattern.findall(returns)
        return returns

    @staticmethod
    def check_and_parse_optional(param_type: str) -> Tuple[bool, str]:
        return "optional" in param_type, param_type.replace(", optional", "")

    @staticmethod
    def check_and_parse_default_value(param_desc: str) -> Tuple[bool, str]:
        default_val = re.search(r"Defaults to (.+?)\.", param_desc)
        return (True, default_val.group(1)) if default_val else (False, "")

    @staticmethod
    def check_and_parse_enum(param_desc: str) -> Tuple[bool, str]:
        enum_val = re.search(r"Enum: \[(.+?)\]", param_desc)
        return (True, [e.strip() for e in enum_val.group(1).split(",")]) if enum_val else (False, [])

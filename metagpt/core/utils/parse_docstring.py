import re
from typing import Tuple


def remove_spaces(text):
    return re.sub(r"\s+", " ", text).strip() if text else ""


class DocstringParser:
    @staticmethod
    def parse(docstring: str) -> Tuple[str, str]:
        """Parse the docstring and return the overall description and the parameter description.

        Args:
            docstring (str): The docstring to be parsed.

        Returns:
            Tuple[str, str]: A tuple of (overall description, parameter description)
        """


class reSTDocstringParser(DocstringParser):
    """A parser for reStructuredText (reST) docstring"""


class GoogleDocstringParser(DocstringParser):
    """A parser for Google-stype docstring"""

    @staticmethod
    def parse(docstring: str) -> Tuple[str, str]:
        if not docstring:
            return "", ""

        docstring = remove_spaces(docstring)

        if "Args:" in docstring:
            overall_desc, param_desc = docstring.split("Args:")
            param_desc = "Args:" + param_desc
        else:
            overall_desc = docstring
            param_desc = ""

        return overall_desc, param_desc

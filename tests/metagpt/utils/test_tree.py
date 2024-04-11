from pathlib import Path
from typing import List

import pytest

from metagpt.utils.tree import _print_tree, tree


@pytest.mark.parametrize(
    ("root", "rules"),
    [
        (str(Path(__file__).parent / "../.."), None),
        (str(Path(__file__).parent / "../.."), str(Path(__file__).parent / "../../../.gitignore")),
    ],
)
def test_tree(root: str, rules: str):
    v = tree(root=root, gitignore=rules)
    assert v


@pytest.mark.parametrize(
    ("root", "rules"),
    [
        (str(Path(__file__).parent / "../.."), None),
        (str(Path(__file__).parent / "../.."), str(Path(__file__).parent / "../../../.gitignore")),
    ],
)
def test_tree_command(root: str, rules: str):
    v = tree(root=root, gitignore=rules, run_command=True)
    assert v


@pytest.mark.parametrize(
    ("tree", "want"),
    [
        ({"a": {"b": {}, "c": {}}}, ["a", "+-- b", "+-- c"]),
        ({"a": {"b": {}, "c": {"d": {}}}}, ["a", "+-- b", "+-- c", "    +-- d"]),
        (
            {"a": {"b": {"e": {"f": {}, "g": {}}}, "c": {"d": {}}}},
            ["a", "+-- b", "|   +-- e", "|       +-- f", "|       +-- g", "+-- c", "    +-- d"],
        ),
        (
            {"h": {"a": {"b": {"e": {"f": {}, "g": {}}}, "c": {"d": {}}}, "i": {}}},
            [
                "h",
                "+-- a",
                "|   +-- b",
                "|   |   +-- e",
                "|   |       +-- f",
                "|   |       +-- g",
                "|   +-- c",
                "|       +-- d",
                "+-- i",
            ],
        ),
    ],
)
def test__print_tree(tree: dict, want: List[str]):
    v = _print_tree(tree)
    assert v == want


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

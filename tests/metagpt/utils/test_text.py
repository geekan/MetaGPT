import pytest

from metagpt.utils.text import (
    decode_unicode_escape,
    generate_prompt_chunk,
    reduce_message_length,
    split_paragraph,
)


def _msgs():
    length = 20
    while length:
        yield "Hello," * 1000 * length
        length -= 1


def _paragraphs(n):
    return " ".join("Hello World." for _ in range(n))


@pytest.mark.parametrize(
    "msgs, model_name, system_text, reserved, expected",
    [
        (_msgs(), "gpt-3.5-turbo-0613", "System", 1500, 1),
        (_msgs(), "gpt-3.5-turbo-16k", "System", 3000, 6),
        (_msgs(), "gpt-3.5-turbo-16k", "Hello," * 1000, 3000, 5),
        (_msgs(), "gpt-4", "System", 2000, 3),
        (_msgs(), "gpt-4", "Hello," * 1000, 2000, 2),
        (_msgs(), "gpt-4-32k", "System", 4000, 14),
        (_msgs(), "gpt-4-32k", "Hello," * 2000, 4000, 12),
    ],
)
def test_reduce_message_length(msgs, model_name, system_text, reserved, expected):
    length = len(reduce_message_length(msgs, model_name, system_text, reserved)) / (len("Hello,")) / 1000
    assert length == expected


@pytest.mark.parametrize(
    "text, prompt_template, model_name, system_text, reserved, expected",
    [
        (" ".join("Hello World." for _ in range(1000)), "Prompt: {}", "gpt-3.5-turbo-0613", "System", 1500, 2),
        (" ".join("Hello World." for _ in range(1000)), "Prompt: {}", "gpt-3.5-turbo-16k", "System", 3000, 1),
        (" ".join("Hello World." for _ in range(4000)), "Prompt: {}", "gpt-4", "System", 2000, 2),
        (" ".join("Hello World." for _ in range(8000)), "Prompt: {}", "gpt-4-32k", "System", 4000, 1),
        (" ".join("Hello World" for _ in range(8000)), "Prompt: {}", "gpt-3.5-turbo-0613", "System", 1000, 8),
    ],
)
def test_generate_prompt_chunk(text, prompt_template, model_name, system_text, reserved, expected):
    chunk = len(list(generate_prompt_chunk(text, prompt_template, model_name, system_text, reserved)))
    assert chunk == expected


@pytest.mark.parametrize(
    "paragraph, sep, count, expected",
    [
        (_paragraphs(10), ".", 2, [_paragraphs(5), f" {_paragraphs(5)}"]),
        (_paragraphs(10), ".", 3, [_paragraphs(4), f" {_paragraphs(3)}", f" {_paragraphs(3)}"]),
        (f"{_paragraphs(5)}\n{_paragraphs(3)}", "\n.", 2, [f"{_paragraphs(5)}\n", _paragraphs(3)]),
        ("......", ".", 2, ["...", "..."]),
        ("......", ".", 3, ["..", "..", ".."]),
        (".......", ".", 2, ["....", "..."]),
    ],
)
def test_split_paragraph(paragraph, sep, count, expected):
    ret = split_paragraph(paragraph, sep, count)
    assert ret == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello\\nWorld", "Hello\nWorld"),
        ("Hello\\tWorld", "Hello\tWorld"),
        ("Hello\\u0020World", "Hello World"),
    ],
)
def test_decode_unicode_escape(text, expected):
    assert decode_unicode_escape(text) == expected

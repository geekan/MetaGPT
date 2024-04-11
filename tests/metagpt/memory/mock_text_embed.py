#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import numpy as np

dim = 1536  # openai embedding dim
embed_zeros_arrr = np.zeros(shape=[1, dim]).tolist()
embed_ones_arrr = np.ones(shape=[1, dim]).tolist()

text_embed_arr = [
    {"text": "Write a cli snake game", "embed": embed_zeros_arrr},  # mock data, same as below
    {"text": "Write a game of cli snake", "embed": embed_zeros_arrr},
    {"text": "Write a 2048 web game", "embed": embed_ones_arrr},
    {"text": "Write a Battle City", "embed": embed_ones_arrr},
    {
        "text": "The user has requested the creation of a command-line interface (CLI) snake game",
        "embed": embed_zeros_arrr,
    },
    {"text": "The request is command-line interface (CLI) snake game", "embed": embed_zeros_arrr},
    {
        "text": "Incorporate basic features of a snake game such as scoring and increasing difficulty",
        "embed": embed_ones_arrr,
    },
]

text_idx_dict = {item["text"]: idx for idx, item in enumerate(text_embed_arr)}


def mock_openai_embed_documents(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
    idx = text_idx_dict.get(texts[0])
    embed = text_embed_arr[idx].get("embed")
    return embed


def mock_openai_embed_document(self, text: str) -> list[float]:
    embeds = mock_openai_embed_documents(self, [text])
    return embeds[0]


async def mock_openai_aembed_document(self, text: str) -> list[float]:
    return mock_openai_embed_document(self, text)

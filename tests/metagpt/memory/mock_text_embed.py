#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from typing import Optional

import numpy as np

dim = 1536  # openai embedding dim

text_embed_arr = [
    {"text": "Write a cli snake game", "embed": np.zeros(shape=[1, dim])},  # mock data, same as below
    {"text": "Write a game of cli snake", "embed": np.zeros(shape=[1, dim])},
    {"text": "Write a 2048 web game", "embed": np.ones(shape=[1, dim])},
    {"text": "Write a Battle City", "embed": np.ones(shape=[1, dim])},
    {
        "text": "The user has requested the creation of a command-line interface (CLI) snake game",
        "embed": np.zeros(shape=[1, dim]),
    },
    {"text": "The request is command-line interface (CLI) snake game", "embed": np.zeros(shape=[1, dim])},
    {
        "text": "Incorporate basic features of a snake game such as scoring and increasing difficulty",
        "embed": np.ones(shape=[1, dim]),
    },
]

text_idx_dict = {item["text"]: idx for idx, item in enumerate(text_embed_arr)}


def mock_openai_embed_documents(self, texts: list[str], chunk_size: Optional[int] = 0) -> list[list[float]]:
    idx = text_idx_dict.get(texts[0])
    embed = text_embed_arr[idx].get("embed")
    return embed

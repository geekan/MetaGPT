# -*- coding: utf-8 -*-
# @Date    : 2023/7/22 02:40
# @Author  : stellahong (stellahong@fuzhi.ai)
#

import pytest
from typing import List
from metagpt.actions.design import SDPromptOptimize, SDPromptImprove
from metagpt.actions.ui_design import ModelSelection


@pytest.mark.asyncio
async def test_ui_model_selection():
    ms = ModelSelection()
    model_name, domain = await ms.run("Pokémon Go")
    assert model_name == "pixelmix_v10"


@pytest.mark.asyncio
async def test_ui_sd_generation():
    pass


@pytest.mark.asyncio
async def test_ui_sd_prompt_optimize():
    sd_po = SDPromptOptimize()
    resp = await sd_po.run(query="Pokémon Go", domain="Anime", answer_count=1)
    assert type(resp) == List
    assert len(resp) == 1


@pytest.mark.asyncio
async def test_ui_sd_optimize_answer_count():
    sd_po = SDPromptOptimize()
    answer_count = 2
    resp = await sd_po.run(query="Pokémon Go", domain="Anime", answer_count=2)
    assert type(resp) == List
    assert len(resp) == answer_count

@pytest.mark.asyncio
async def test_ui_sd_improve_answer_count():
    sd_pi = SDPromptImprove()
    answer_count = 2
    resp = await sd_pi.run(query="Pokémon Go", domain="Anime", answer_count=2)
    assert type(resp) == List
    assert len(resp) == answer_count
    

@pytest.mark.asyncio
async def test_ui_sd_prompt_improve():
    sd_pi = SDPromptImprove()
    resp = await sd_pi.run(query="Pokémon Go", domain="Anime", answer_count=1)
    assert type(resp) == List
    assert len(resp) == 1

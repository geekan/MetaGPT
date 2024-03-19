#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : test_gpt_v_generator.py
"""
from pathlib import Path

import pytest

from metagpt import logs
from metagpt.const import METAGPT_ROOT
from metagpt.tools.libs.gpt_v_generator import GPTvGenerator


@pytest.fixture
def mock_webpage_filename_with_styles_and_scripts(mocker):
    mock_data = """```html\n<html>\n<script src="scripts.js"></script>
<link rel="stylesheet" href="styles.css">\n</html>\n```\n
```css\n/* styles.css */\n```\n
```javascript\n// scripts.js\n```\n"""
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", return_value=mock_data)
    return mocker


@pytest.fixture
def mock_webpage_filename_with_style_and_script(mocker):
    mock_data = """```html\n<html>\n<script src="script.js"></script>
<link rel="stylesheet" href="style.css">\n</html>\n```\n
```css\n/* style.css */\n```\n
```javascript\n// script.js\n```\n"""
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", return_value=mock_data)
    return mocker


@pytest.fixture
def mock_image_layout(mocker):
    image_layout = "The layout information of the sketch image is ..."
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", return_value=image_layout)
    return mocker


@pytest.fixture
def image_path():
    return f"{METAGPT_ROOT}/docs/resources/workspace/content_rec_sys/resources/competitive_analysis.png"


@pytest.mark.asyncio
async def test_generate_webpages(mock_webpage_filename_with_styles_and_scripts, image_path):
    generator = GPTvGenerator()
    rsp = await generator.generate_webpages(image_path=image_path)
    logs.logger.info(rsp)
    assert "html" in rsp
    assert "css" in rsp
    assert "javascript" in rsp


@pytest.mark.asyncio
async def test_save_webpages_with_styles_and_scripts(mock_webpage_filename_with_styles_and_scripts, image_path):
    generator = GPTvGenerator()
    webpages = await generator.generate_webpages(image_path)
    webpages_dir = generator.save_webpages(webpages=webpages, save_folder_name="test_1")
    logs.logger.info(webpages_dir)
    assert webpages_dir.exists()
    assert (webpages_dir / "index.html").exists()
    assert (webpages_dir / "styles.css").exists()
    assert (webpages_dir / "scripts.js").exists()


@pytest.mark.asyncio
async def test_save_webpages_with_style_and_script(mock_webpage_filename_with_style_and_script, image_path):
    generator = GPTvGenerator()
    webpages = await generator.generate_webpages(image_path)
    webpages_dir = generator.save_webpages(webpages=webpages, save_folder_name="test_2")
    logs.logger.info(webpages_dir)
    assert webpages_dir.exists()
    assert (webpages_dir / "index.html").exists()
    assert (webpages_dir / "style.css").exists()
    assert (webpages_dir / "script.js").exists()


@pytest.mark.asyncio
async def test_analyze_layout(mock_image_layout, image_path):
    layout = await GPTvGenerator().analyze_layout(Path(image_path))
    logs.logger.info(layout)
    assert layout


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : test_gpt_v_generator.py
"""
import pytest

from metagpt import logs
from metagpt.tools.libs.gpt_v_generator import GPTvGenerator


@pytest.fixture
def mock_webpages(mocker):
    mock_data = """```html\n<html>\n<script src="scripts.js"></script>
<link rel="stylesheet" href="styles.css(">\n</html>\n```\n
```css\n.class { ... }\n```\n
```javascript\nfunction() { ... }\n```\n"""
    mocker.patch("metagpt.tools.libs.gpt_v_generator.GPTvGenerator.generate_webpages", return_value=mock_data)
    return mocker


def test_vision_generate_webpages(mock_webpages):
    image_path = "image.png"
    generator = GPTvGenerator()
    rsp = generator.generate_webpages(image_path=image_path)
    logs.logger.info(rsp)
    assert "html" in rsp
    assert "css" in rsp
    assert "javascript" in rsp


def test_save_webpages(mock_webpages):
    image_path = "image.png"
    generator = GPTvGenerator()
    webpages = generator.generate_webpages(image_path)
    webpages_dir = generator.save_webpages(image_path=image_path, webpages=webpages)
    logs.logger.info(webpages_dir)
    assert webpages_dir.exists()

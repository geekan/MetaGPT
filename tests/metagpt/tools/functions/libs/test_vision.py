#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : test_vision.py
"""
import pytest

from metagpt import logs
from metagpt.tools.functions.libs.vision import Vision


@pytest.fixture
def mock_webpages():
    return """```html\n<html>\n<script src="scripts.js"></script>
<link rel="stylesheet" href="styles.css(">\n</html>\n```\n
```css\n.class { ... }\n```\n
```javascript\nfunction() { ... }\n```\n"""


def test_vision_generate_webpages(mocker, mock_webpages):
    mocker.patch(
        "metagpt.tools.functions.libs.vision.Vision.generate_web_pages",
        return_value=mock_webpages
    )
    image_path = "image.png"
    vision = Vision()
    rsp = vision.generate_web_pages(image_path=image_path)
    logs.logger.info(rsp)
    assert "html" in rsp
    assert "css" in rsp
    assert "javascript" in rsp


def test_save_webpages(mocker, mock_webpages):
    mocker.patch(
        "metagpt.tools.functions.libs.vision.Vision.generate_web_pages",
        return_value=mock_webpages
    )
    image_path = "image.png"
    vision = Vision()
    webpages = vision.generate_web_pages(image_path)
    webpages_dir = vision.save_webpages(image_path=image_path, webpages=webpages)
    logs.logger.info(webpages_dir)
    assert webpages_dir.exists()



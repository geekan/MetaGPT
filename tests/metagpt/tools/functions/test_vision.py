#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : test_vision.py
"""
import base64
from unittest.mock import AsyncMock

from pytest_mock import mocker

from metagpt import logs
from metagpt.tools.functions.libs.vision import Vision


def test_vision_generate_web_pages():
    image_path = "./image.png"
    vision = Vision()
    rsp = vision.generate_web_pages(image_path=image_path)
    logs.logger.info(rsp)
    assert "html" in rsp
    assert "css" in rsp
    assert "javascript" in rsp


def test_save_webpages():
    image_path = "./image.png"
    vision = Vision()
    webpages = """```html: <html>\n<script src="scripts.js"></script>
    <link rel="stylesheet" href="styles.css(">\n</html>```
    "```css: .class { ... } ```\n ```javascript: function() { ... }```"""
    webpages_dir = vision.save_webpages(image_path=image_path, webpages=webpages)
    logs.logger.info(webpages_dir)
    assert webpages_dir.exists()
    assert (webpages_dir / "index.html").exists()
    assert (webpages_dir / "style.css").exists() or (webpages_dir / "styles.css").exists()
    assert (webpages_dir / "script.js").exists() or (webpages_dir / "scripts.js").exists()



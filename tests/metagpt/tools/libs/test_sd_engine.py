# -*- coding: utf-8 -*-
# @Date    : 1/10/2024 10:07 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import base64
import io
import json

import pytest
from PIL import Image, ImageDraw

from metagpt.tools.libs.sd_engine import SDEngine


def generate_mock_image_data():
    # 创建一个简单的图片对象
    image = Image.new("RGB", (100, 100), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "Mock Image", fill="black")

    # 将图片转换为二进制数据
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        image_binary = buffer.getvalue()

    # 对图片二进制数据进行 base64 编码
    image_base64 = base64.b64encode(image_binary).decode("utf-8")

    return image_base64


def test_sd_tools(mocker):
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {"images": [generate_mock_image_data()]}
    mocker.patch("requests.Session.post", return_value=mock_response)

    engine = SDEngine(sd_url="http://example_localhost:7860")
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    engine.simple_run_t2i(engine.payload)


def test_sd_construct_payload():
    engine = SDEngine(sd_url="http://example_localhost:7860")
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    assert "negative_prompt" in engine.payload


@pytest.mark.asyncio
async def test_sd_asyn_t2i(mocker):
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_response = mocker.AsyncMock()
    mock_response.read.return_value = json.dumps({"images": [generate_mock_image_data()]})
    mock_post.return_value.__aenter__.return_value = mock_response

    engine = SDEngine(sd_url="http://example_localhost:7860")
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    await engine.run_t2i([engine.payload])
    assert "negative_prompt" in engine.payload

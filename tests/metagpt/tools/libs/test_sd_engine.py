# -*- coding: utf-8 -*-
# @Date    : 1/10/2024 10:07 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import base64
import io

import pytest
from aioresponses import aioresponses
from PIL import Image, ImageDraw
from requests_mock import Mocker

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


def test_sd_tools():
    engine = SDEngine(sd_url="http://localhost:7860")
    # 使用 requests_mock.Mocker 替换 simple_run_t2i 的网络请求
    mock_imgs = generate_mock_image_data()
    with Mocker() as mocker:
        # 指定模拟请求的返回值
        mocker.post(engine.sd_t2i_url, json={"images": [mock_imgs]})

        # 在被测试代码中调用 simple_run_t2i
        result = engine.simple_run_t2i(engine.payload)

    # 断言结果是否是指定的 Mock 返回值
    assert len(result) == 1


def test_sd_construct_payload():
    engine = SDEngine(sd_url="http://localhost:7860")
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    assert "negative_prompt" in engine.payload


@pytest.mark.asyncio
async def test_sd_asyn_t2i():
    engine = SDEngine(sd_url="http://example.com/mock_sd_t2i")

    prompt = "1boy, hansom"
    engine.construct_payload(prompt)
    # 构建mock数据
    mock_imgs = generate_mock_image_data()

    mock_responses = aioresponses()

    # 手动启动模拟
    mock_responses.start()

    try:
        # 指定模拟请求的返回值
        mock_responses.post("http://example.com/mock_sd_t2i/sdapi/v1/txt2img", payload={"images": [mock_imgs]})

        # 在被测试代码中调用异步函数 run_t2i
        await engine.run_t2i([engine.payload])

    finally:
        # 手动停止模拟
        mock_responses.stop()

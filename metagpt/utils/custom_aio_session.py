#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 16:43
@Author  : alexanderwu
@File    : custom_aio_session.py
"""

import ssl
import aiohttp
import openai


class CustomAioSession:
    async def __aenter__(self):
        """暂时使用自签署的ssl，先忽略验证问题"""
        # ssl_context = ssl.create_default_context()
        # ssl_context.check_hostname = False
        # ssl_context.verify_mode = ssl.CERT_NONE
        headers = {"Accept-Encoding": "identity"}  # Disable gzip encoding
        custom_session = aiohttp.ClientSession(headers=headers)
        openai.aiosession.set(custom_session)
        return custom_session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        session = openai.aiosession.get()
        if session:
            await session.close()
            openai.aiosession.set(None)

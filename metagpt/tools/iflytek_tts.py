#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : iflytek_tts.py
@Desc    : iFLYTEK TTS OAS3 api, which provides text-to-speech functionality
"""
import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from time import mktime
from typing import Optional
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import aiofiles
import websockets as websockets
from pydantic import BaseModel

from metagpt.logs import logger


class IFlyTekTTSStatus(Enum):
    STATUS_FIRST_FRAME = 0  # The first frame
    STATUS_CONTINUE_FRAME = 1  # The intermediate frame
    STATUS_LAST_FRAME = 2  # The last frame


class AudioData(BaseModel):
    audio: str
    status: int
    ced: str


class IFlyTekTTSResponse(BaseModel):
    code: int
    message: str
    data: Optional[AudioData] = None
    sid: str


DEFAULT_IFLYTEK_VOICE = "xiaoyan"


class IFlyTekTTS(object):
    def __init__(self, app_id: str, api_key: str, api_secret: str):
        """
        :param app_id: Application ID is used to access your iFlyTek service API, see: `https://console.xfyun.cn/services/tts`
        :param api_key: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
        :param api_secret: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
        """
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret

    async def synthesize_speech(self, text, output_file: str, voice=DEFAULT_IFLYTEK_VOICE):
        url = self._create_url()
        data = {
            "common": {"app_id": self.app_id},
            "business": {"aue": "lame", "sfl": 1, "auf": "audio/L16;rate=16000", "vcn": voice, "tte": "utf8"},
            "data": {"status": 2, "text": str(base64.b64encode(text.encode("utf-8")), "UTF8")},
        }
        req = json.dumps(data)
        async with websockets.connect(url) as websocket:
            # send request
            await websocket.send(req)

            # receive frames
            async with aiofiles.open(str(output_file), "wb") as writer:
                while True:
                    v = await websocket.recv()
                    rsp = IFlyTekTTSResponse(**json.loads(v))
                    if rsp.data:
                        binary_data = base64.b64decode(rsp.data.audio)
                        await writer.write(binary_data)
                        if rsp.data.status != IFlyTekTTSStatus.STATUS_LAST_FRAME.value:
                            continue
                    break

    def _create_url(self):
        """Create request url"""
        url = "wss://tts-api.xfyun.cn/v2/tts"
        # Generate a timestamp in RFC1123 format
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # Perform HMAC-SHA256 encryption
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"), signature_origin.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self.api_key,
            "hmac-sha256",
            "host date request-line",
            signature_sha,
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(encoding="utf-8")
        # Combine the authentication parameters of the request into a dictionary.
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        # Concatenate the authentication parameters to generate the URL.
        url = url + "?" + urlencode(v)
        return url


# Export
async def oas3_iflytek_tts(text: str, voice: str = "", app_id: str = "", api_key: str = "", api_secret: str = ""):
    """Text to speech
    For more details, check out:`https://www.xfyun.cn/doc/tts/online_tts/API.html`

    :param voice: Default `xiaoyan`. For more details, checkout: `https://www.xfyun.cn/doc/tts/online_tts/API.html#%E6%8E%A5%E5%8F%A3%E8%B0%83%E7%94%A8%E6%B5%81%E7%A8%8B`
    :param text: The text used for voice conversion.
    :param app_id: Application ID is used to access your iFlyTek service API, see: `https://console.xfyun.cn/services/tts`
    :param api_key: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
    :param api_secret: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
    :return: Returns the Base64-encoded .mp3 file data if successful, otherwise an empty string.

    """

    filename = Path(__file__).parent / (uuid.uuid4().hex + ".mp3")
    try:
        tts = IFlyTekTTS(app_id=app_id, api_key=api_key, api_secret=api_secret)
        await tts.synthesize_speech(text=text, output_file=str(filename), voice=voice)
        async with aiofiles.open(str(filename), mode="rb") as reader:
            data = await reader.read()
            base64_string = base64.b64encode(data).decode("utf-8")
    except Exception as e:
        logger.error(f"text:{text}, error:{e}")
        base64_string = ""
    finally:
        filename.unlink(missing_ok=True)

    return base64_string

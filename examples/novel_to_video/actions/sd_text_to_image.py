# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :
import asyncio
import base64
import io
import json
import pathlib
from datetime import datetime
from os.path import join

from aiohttp import ClientSession
from PIL import Image, PngImagePlugin

from metagpt.actions import Action
from metagpt.logs import logger

payload = {
    "prompt": "",
    "negative_prompt": "",
    "override_settings": {"sd_model_checkpoint": "anything-v5-PrtRE"},
    "seed": -1,
    "batch_size": 1,
    "n_iter": 1,
    "steps": 20,
    "cfg_scale": 7,
    "width": 512,
    "height": 768,
    "restore_faces": False,
    "tiling": False,
    "do_not_save_samples": False,
    "do_not_save_grid": False,
    "enable_hr": False,
    "hr_scale": 2,
    "hr_upscaler": "Latent",
    "hr_second_pass_steps": 0,
    "hr_resize_x": 0,
    "hr_resize_y": 0,
    "hr_upscale_to_x": 0,
    "hr_upscale_to_y": 0,
    "truncate_x": 0,
    "truncate_y": 0,
    "applied_old_hires_behavior_to": None,
    "eta": None,
    "sampler_index": "DPM++ 2M Karras",
    "alwayson_scripts": {},
}

default_negative_prompt = ('EasyNegative,NSFW,lowres, bad anatomy, bad hands, text, error, missing fingers, '
                           'extra digit, fewer digits, cropped, worst quality, low quality, normal quality, '
                           'jpeg artifacts, signature, watermark, username, blurry')

default_quality_prompt = 'masterpiece, best quality,'


class SDEngine:
    def __init__(self):
        # Initialize the SDEngine with configuration
        self.sd_url = "http://127.0.0.1:7860"
        self.sd_t2i_url = f"{self.sd_url}/sdapi/v1/txt2img"
        # Define default payload settings for SD API
        self.payload = payload
        logger.info(self.sd_t2i_url)

    def construct_payload(
            self,
            prompt,
            negative_prompt=default_negative_prompt,
            width=768,
            height=512,
            sd_model="anything-v5-PrtRE",
    ):
        # Configure the payload with provided inputs
        self.payload["prompt"] = default_quality_prompt+prompt
        self.payload["negative_prompt"] = negative_prompt
        self.payload["width"] = width
        self.payload["height"] = height
        self.payload["override_settings"]["sd_model_checkpoint"] = sd_model
        logger.info(f"call sd payload is {self.payload}")
        return self.payload

    def _save(self, imgs, save_dir='.', save_name=""):
        save_dir = pathlib.Path(save_dir)
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        batch_decode_base64_to_image(imgs, str(save_dir), save_name=save_name)

    async def run_t2i(self, output_dir: str = '.'):
        # Asynchronously run the SD API for multiple prompts
        session = ClientSession()
        results = await self.run(url=self.sd_t2i_url, payload=self.payload, session=session)
        payload_idx = datetime.now().strftime("%Y%m%d%H%M%S")
        self._save(results, save_dir=output_dir, save_name=f"output_{payload_idx}")
        await session.close()

    async def run(self, url, payload, session):
        # Perform the HTTP POST request to the SD API
        async with session.post(url, json=payload, timeout=600) as rsp:
            data = await rsp.read()

        rsp_json = json.loads(data)
        # print('rsp_json:', rsp_json)
        imgs = rsp_json["images"]
        logger.info(f"callback rsp json is {rsp_json.keys()}")
        return imgs


def decode_base64_to_image(img, save_name):
    image = Image.open(io.BytesIO(base64.b64decode(img.split(",", 1)[0])))
    pnginfo = PngImagePlugin.PngInfo()
    logger.info(save_name)
    image.save(f"{save_name}.png", pnginfo=pnginfo)
    return pnginfo, image


def batch_decode_base64_to_image(imgs, save_dir="", save_name=""):
    for idx, _img in enumerate(imgs):
        save_name = join(save_dir, save_name)
        decode_base64_to_image(_img, save_name=save_name)


# SD_t2i SD文生图
class SD_t2i(Action):
    sd_model: str = "anything-v5-PrtRE"
    save_path: str = ""
    prompts: str = ""

    def __init__(self, name: str = "", sd_model: str = "anything-v5-PrtRE", prompts: str = "", save_path: str = "",
                 *args,
                 **kwargs):
        super().__init__(**kwargs)
        self.prompts = prompts
        self.sd_model = sd_model
        self.save_path = save_path

    async def run(self, *args, **kwargs) -> str:
        # 初始化SD引擎
        sd_Engine = SDEngine()
        sd_Engine.construct_payload(prompt=self.prompts, sd_model=self.sd_model)
        await sd_Engine.run_t2i(self.save_path)
        resp = self.prompts
        return resp


async def main():
    prompt = "1boy, police station, interrogation, suspicion, explanation, misunderstanding, mistake, newcomer, questioning, doubt, disbelief, confusion, accusation, misunderstanding, disbelief, suspicion"
    action = SD_t2i(save_path="../../workspace/12345", prompts=prompt)
    await action.run()


if __name__ == '__main__':
    asyncio.run(main())

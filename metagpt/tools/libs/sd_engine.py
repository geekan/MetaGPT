# -*- coding: utf-8 -*-
# @Date    : 2023/7/19 16:28
# @Author  : stellahong (stellahong@deepwisdom.ai)
# @Desc    :
from __future__ import annotations

import base64
import hashlib
import io
import json
from os.path import join

import requests
from aiohttp import ClientSession
from PIL import Image, PngImagePlugin

#
from metagpt.const import SD_OUTPUT_FILE_REPO, SOURCE_ROOT
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.tools.tool_type import ToolType

payload = {
    "prompt": "",
    "negative_prompt": "(easynegative:0.8),black, dark,Low resolution",
    "override_settings": {"sd_model_checkpoint": "galaxytimemachinesGTM_photoV20"},
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
    "sampler_index": "DPM++ SDE Karras",
    "alwayson_scripts": {},
}

default_negative_prompt = "(easynegative:0.8),black, dark,Low resolution"


@register_tool(
    tool_type=ToolType.STABLE_DIFFUSION.type_name,
    include_functions=["__init__", "simple_run_t2i", "run_t2i", "construct_payload", "save"],
)
class SDEngine:
    """Generate image using stable diffusion model.

    This class provides methods to interact with a stable diffusion service to generate images based on text inputs.
    """

    def __init__(self, sd_url=""):
        """Initialize the SDEngine instance with configuration.

        Args:
            sd_url (str, optional): URL of the stable diffusion service. Defaults to "".
        """
        self.sd_url = sd_url
        self.sd_t2i_url = f"{self.sd_url}/sdapi/v1/txt2img"
        # Define default payload settings for SD API
        self.payload = payload
        logger.info(self.sd_t2i_url)

    def construct_payload(
        self,
        prompt,
        negtive_prompt=default_negative_prompt,
        width=512,
        height=512,
        sd_model="galaxytimemachinesGTM_photoV20",
    ):
        """Modify and set the API parameters for image generation.

        Args:
            prompt (str): Text input for image generation.
            negtive_prompt (str, optional): Text input for negative prompts. Defaults to None.
            width (int, optional): Width of the generated image in pixels. Defaults to 512.
            height (int, optional): Height of the generated image in pixels. Defaults to 512.
            sd_model (str, optional): The model to use for image generation. Defaults to "galaxytimemachinesGTM_photoV20".

        Returns:
            dict: Updated parameters for the stable diffusion API.
        """
        self.payload["prompt"] = prompt
        self.payload["negative_prompt"] = negtive_prompt
        self.payload["width"] = width
        self.payload["height"] = height
        self.payload["override_settings"]["sd_model_checkpoint"] = sd_model
        logger.info(f"call sd payload is {self.payload}")
        return self.payload

    def save(self, imgs, save_name=""):
        """Save generated images to the output directory.

        Args:
            imgs (str): Generated images.
            save_name (str, optional): Output image name. Default is empty.
        """
        save_dir = SOURCE_ROOT / SD_OUTPUT_FILE_REPO
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        batch_decode_base64_to_image(imgs, str(save_dir), save_name=save_name)

    def simple_run_t2i(self, payload: dict, auto_save: bool = True):
        """Run the stable diffusion API for multiple prompts, calling the stable diffusion API to generate images.

        Args:
            payload (dict): Dictionary of input parameters for the stable diffusion API.
            auto_save (bool, optional): Save generated images automatically. Defaults to True.

        Returns:
            list: The generated images as a result of the API call.
        """
        with requests.Session() as session:
            logger.debug(self.sd_t2i_url)
            rsp = session.post(self.sd_t2i_url, json=payload, timeout=600)

        results = rsp.json()["images"]
        if auto_save:
            save_name = hashlib.sha256(payload["prompt"][:10].encode()).hexdigest()[:6]
            self.save(results, save_name=f"output_{save_name}")
        return results

    async def run_t2i(self, payloads: list):
        """Run the stable diffusion API for multiple prompts asynchronously.

        Args:
            payloads (list): list of payload, each payload is a dictionary of input parameters for the stable diffusion API.
        """
        session = ClientSession()
        for payload_idx, payload in enumerate(payloads):
            results = await self.run(url=self.sd_t2i_url, payload=payload, session=session)
            self.save(results, save_name=f"output_{payload_idx}")
        await session.close()

    async def run(self, url, payload, session):
        """Perform the HTTP POST request to the SD API.

        Args:
            url (str): The API URL.
            payload (dict): The payload for the request.
            session (ClientSession): The session for making HTTP requests.

        Returns:
            list: Images generated by the stable diffusion API.
        """
        async with session.post(url, json=payload, timeout=600) as rsp:
            data = await rsp.read()

        rsp_json = json.loads(data)
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

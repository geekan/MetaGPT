#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : use gpt4v to improve prompt and draw image with dall-e-3

"""set `model: "gpt-4-vision-preview"` in `config2.yaml` first"""

import asyncio

from PIL import Image

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.utils.common import encode_image


class GenAndImproveImageAction(Action):
    save_image: bool = True

    async def generate_image(self, prompt: str) -> Image:
        imgs = await self.llm.gen_image(model="dall-e-3", prompt=prompt)
        return imgs[0]

    async def refine_prompt(self, old_prompt: str, image: Image) -> str:
        msg = (
            f"You are a creative painter, with the given generated image and old prompt: {old_prompt}, "
            f"please refine the prompt and generate new one. Just output the new prompt."
        )
        b64_img = encode_image(image)
        new_prompt = await self.llm.aask(msg=msg, images=[b64_img])
        return new_prompt

    async def evaluate_images(self, old_prompt: str, images: list[Image]) -> str:
        msg = (
            "With the prompt and two generated image, to judge if the second one is better than the first one. "
            "If so, just output True else output False"
        )
        b64_imgs = [encode_image(img) for img in images]
        res = await self.llm.aask(msg=msg, images=b64_imgs)
        return res

    async def run(self, messages: list[Message]) -> str:
        prompt = messages[-1].content

        old_img: Image = await self.generate_image(prompt)
        new_prompt = await self.refine_prompt(old_prompt=prompt, image=old_img)
        logger.info(f"original prompt: {prompt}")
        logger.info(f"refined prompt: {new_prompt}")
        new_img: Image = await self.generate_image(new_prompt)
        if self.save_image:
            old_img.save("./img_by-dall-e_old.png")
            new_img.save("./img_by-dall-e_new.png")
        res = await self.evaluate_images(old_prompt=prompt, images=[old_img, new_img])
        opinion = f"The second generated image is better than the first one: {res}"
        logger.info(f"evaluate opinion: {opinion}")
        return opinion


class Painter(Role):
    name: str = "MaLiang"
    profile: str = "Painter"
    goal: str = "to generate fine painting"

    def __init__(self, **data):
        super().__init__(**data)

        self.set_actions([GenAndImproveImageAction])


async def main():
    role = Painter()
    await role.run(with_message="a girl with flowers")


if __name__ == "__main__":
    asyncio.run(main())

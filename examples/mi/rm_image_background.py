import asyncio

from metagpt.roles.mi.interpreter import Interpreter


async def main(requirement: str = ""):
    mi = Interpreter(use_tools=False)
    await mi.run(requirement)


if __name__ == "__main__":
    image_path = "/your/path/to/the/image.jpeg"
    save_path = "/your/intended/save/path/for/image_rm_bg.png"
    requirement = f"This is a image, you need to use python toolkit rembg to remove the background of the image and save the result. image path:{image_path}; save path:{save_path}."
    asyncio.run(main(requirement))

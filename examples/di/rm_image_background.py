import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(requirement: str = ""):
    di = DataInterpreter()
    await di.run(requirement)


if __name__ == "__main__":
    image_path = "/your/path/to/the/image.jpeg"
    save_path = "/your/intended/save/path/for/image_rm_bg.png"
    requirement = f"This is a image, you need to use python toolkit rembg to remove the background of the image and save the result. image path:{image_path}; save path:{save_path}."
    asyncio.run(main(requirement))

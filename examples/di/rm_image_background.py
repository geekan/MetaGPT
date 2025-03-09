import asyncio

from metagpt.const import DEFAULT_WORKSPACE_ROOT, EXAMPLE_DATA_PATH
from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(requirement: str = ""):
    di = DataInterpreter()
    await di.run(requirement)


if __name__ == "__main__":
    image_path = EXAMPLE_DATA_PATH / "di/dog.jpg"
    save_path = DEFAULT_WORKSPACE_ROOT / "image_rm_bg.png"
    requirement = f"This is a image, you need to use python toolkit rembg to remove the background of the image and save the result. image path:{image_path}; save path:{save_path}."
    asyncio.run(main(requirement))

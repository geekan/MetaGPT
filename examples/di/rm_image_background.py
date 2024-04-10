import asyncio

from metagpt.roles.di.mgx import MGX


async def main(requirement: str = ""):
    # di = DataInterpreter()
    di = MGX(use_intent=False, tools=["<all>"])
    await di.run(requirement)


if __name__ == "__main__":
    image_path = r"F:\deepWisdom\metaGPT\hsr\MetaGPT\examples\data\dog.beebf16d.jpg"
    save_path = r"F:\deepWisdom\metaGPT\hsr\MetaGPT\examples\data\/image_rm_bg.png"
    requirement = f"This is a image, you need to use python toolkit rembg to remove the background of the image and save the result. image path:{image_path}; save path:{save_path}."
    asyncio.run(main(requirement))

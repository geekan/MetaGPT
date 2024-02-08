from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main():
    # Notice: pip install metagpt[ocr] before using this example
    image_path = "image.jpg"
    language = "English"
    requirement = f"""This is a {language} invoice image.
    Your goal is to perform OCR on images using PaddleOCR, then extract the total amount from ocr text results, and finally save as table. Image path: {image_path}. 
    NOTE: The environments for Paddle and PaddleOCR are all ready and has been fully installed."""
    ci = CodeInterpreter()

    await ci.run(requirement)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

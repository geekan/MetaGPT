from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    # Notice: pip install metagpt[ocr] before using this example
    image_path = "image.jpg"
    language = "English"
    requirement = f"""This is a {language} receipt image.
    Your goal is to perform OCR on images using PaddleOCR, output text content from the OCR results and discard 
    coordinates and confidence levels, then recognize the total amount from ocr text content, and finally save as table. 
    Image path: {image_path}.
    NOTE: The environments for Paddle and PaddleOCR are all ready and has been fully installed."""
    di = DataInterpreter()

    await di.run(requirement)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

import asyncio

from metagpt.config2 import config
from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.logs import logger
from metagpt.rag.parsers import OmniParse
from metagpt.rag.schema import OmniParseOptions, OmniParseType, ParseResultType
from metagpt.utils.omniparse_client import OmniParseClient

TEST_DOCX = EXAMPLE_DATA_PATH / "omniparse/test01.docx"
TEST_PDF = EXAMPLE_DATA_PATH / "omniparse/test02.pdf"
TEST_VIDEO = EXAMPLE_DATA_PATH / "omniparse/test03.mp4"
TEST_AUDIO = EXAMPLE_DATA_PATH / "omniparse/test04.mp3"


async def omniparse_client_example():
    client = OmniParseClient(base_url=config.omniparse.base_url)

    # docx
    with open(TEST_DOCX, "rb") as f:
        file_input = f.read()
    document_parse_ret = await client.parse_document(file_input=file_input, bytes_filename="test_01.docx")
    logger.info(document_parse_ret)

    # pdf
    pdf_parse_ret = await client.parse_pdf(file_input=TEST_PDF)
    logger.info(pdf_parse_ret)

    # video
    video_parse_ret = await client.parse_video(file_input=TEST_VIDEO)
    logger.info(video_parse_ret)

    # audio
    audio_parse_ret = await client.parse_audio(file_input=TEST_AUDIO)
    logger.info(audio_parse_ret)


async def omniparse_example():
    parser = OmniParse(
        api_key=config.omniparse.api_key,
        base_url=config.omniparse.base_url,
        parse_options=OmniParseOptions(
            parse_type=OmniParseType.PDF,
            result_type=ParseResultType.MD,
            max_timeout=120,
            num_workers=3,
        ),
    )
    ret = parser.load_data(file_path=TEST_PDF)
    logger.info(ret)

    file_paths = [TEST_DOCX, TEST_PDF]
    parser.parse_type = OmniParseType.DOCUMENT
    ret = await parser.aload_data(file_path=file_paths)
    logger.info(ret)


async def main():
    await omniparse_client_example()
    await omniparse_example()


if __name__ == "__main__":
    asyncio.run(main())

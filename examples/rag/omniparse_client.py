import asyncio

from llama_parse import ResultType

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.rag.parser.omniparse.client import OmniParseClient
from metagpt.rag.parser.omniparse.parse import OmniParse
from metagpt.rag.schema import OmniParseOptions, OmniParseType
from metagpt.const import EXAMPLE_DATA_PATH

TEST_DOCX = EXAMPLE_DATA_PATH / "parse/test01.docx"
TEST_PDF = EXAMPLE_DATA_PATH / "parse/test02.pdf"
TEST_VIDEO = EXAMPLE_DATA_PATH / "parse/test03.mp4"
TEST_AUDIO = EXAMPLE_DATA_PATH / "parse/test04.mp3"
TEST_WEBSITE_URL = "https://github.com/geekan/MetaGPT"


async def omniparse_client_example():
    client = OmniParseClient(base_url=config.omniparse.base_url)

    # docx
    with open(TEST_DOCX, "rb") as f:
        filelike = f.read()
    document_parse_ret = await client.parse_document(filelike=filelike, bytes_filename="test_01.docx")
    logger.info(document_parse_ret)

    # pdf
    pdf_parse_ret = await client.parse_pdf(filelike=TEST_PDF)
    logger.info(pdf_parse_ret)

    # video
    video_parse_ret = await client.parse_video(filelike=TEST_VIDEO)
    logger.info(video_parse_ret)

    # audio
    audio_parse_ret = await client.parse_audio(filelike=TEST_AUDIO)
    logger.info(audio_parse_ret)

    # website fixme:omniparse官方api还存在问题
    # website_parse_ret = await client.parse_website(url=TEST_WEBSITE_URL)
    # logger.info(website_parse_ret)


async def omniparse_example():
    parser = OmniParse(
        api_key=config.omniparse.api_key,
        base_url=config.omniparse.base_url,
        parse_options=OmniParseOptions(
            parse_type=OmniParseType.PDF,
            result_type=ResultType.MD,
            max_timeout=120,
            num_workers=3,
        )
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


if __name__ == '__main__':
    asyncio.run(main())

import asyncio

from llama_parse import ResultType

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.rag.parser.omniparse.client import OmniParseClient
from metagpt.rag.parser.omniparse.parse import OmniParse
from metagpt.rag.schema import OmniParseOptions, OmniParseType


async def omniparse_client_example():
    client = OmniParseClient(base_url=config.omniparse.base_url)

    with open("../data/rag/test01.docx", "rb") as f:
        filelike = f.read()
    parse_document_ret = await client.parse_document(filelike=filelike, bytes_filename="test_01.docx")
    logger.info(parse_document_ret)

    parse_pdf_ret = await client.parse_pdf(filelike="../data/rag/test02.pdf")
    logger.info(parse_pdf_ret)


async def omniparse_example():
    parser = OmniParse(
        api_key=config.omniparse.api_key,
        base_url=config.omniparse.base_url,
        parse_options=OmniParseOptions(parse_type=OmniParseType.PDF, result_type=ResultType.MD)
    )
    ret = await parser.aload_data(file_path="../data/rag/test02.pdf")
    logger.info(ret)

    file_paths = ["../data/rag/test01.docx", "../data/rag/test02.pdf"]
    parser.parse_type = OmniParseType.DOCUMENT
    ret = await parser.aload_data(file_path=file_paths)
    logger.info(ret)


async def main():
    await omniparse_client_example()
    await omniparse_example()


if __name__ == '__main__':
    asyncio.run(main())

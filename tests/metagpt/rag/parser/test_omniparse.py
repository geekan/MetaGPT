import pytest

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.rag.parser.omniparse import OmniParseClient
from metagpt.rag.schema import OmniParsedResult


class TestOmniParseClient:
    parse_client = OmniParseClient()

    # test data
    TEST_DOCX = EXAMPLE_DATA_PATH / "parse/test01.docx"
    TEST_PDF = EXAMPLE_DATA_PATH / "parse/test02.pdf"
    TEST_VIDEO = EXAMPLE_DATA_PATH / "parse/test03.mp4"
    TEST_AUDIO = EXAMPLE_DATA_PATH / "parse/test04.mp3"

    @pytest.fixture
    def request_parse(self, mocker):
        return mocker.patch("metagpt.rag.parser.omniparse.OmniParseClient._request_parse")

    @pytest.mark.asyncio
    async def test_parse_pdf(self, request_parse):
        mock_content = "#test title\ntest content"
        mock_parsed_ret = OmniParsedResult(text=mock_content, markdown=mock_content)
        request_parse.return_value = mock_parsed_ret.model_dump()
        parse_ret = await self.parse_client.parse_pdf(self.TEST_PDF)
        assert parse_ret == mock_parsed_ret


class TestOmniParse:
    def test_load_data(self):
        pass

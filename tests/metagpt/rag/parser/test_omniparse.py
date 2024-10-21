import pytest
from llama_index.core import Document

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.rag.parsers import OmniParse
from metagpt.rag.schema import (
    OmniParsedResult,
    OmniParseOptions,
    OmniParseType,
    ParseResultType,
)
from metagpt.utils.omniparse_client import OmniParseClient

# test data
TEST_DOCX = EXAMPLE_DATA_PATH / "omniparse/test01.docx"
TEST_PDF = EXAMPLE_DATA_PATH / "omniparse/test02.pdf"
TEST_VIDEO = EXAMPLE_DATA_PATH / "omniparse/test03.mp4"
TEST_AUDIO = EXAMPLE_DATA_PATH / "omniparse/test04.mp3"


class TestOmniParseClient:
    parse_client = OmniParseClient()

    @pytest.fixture
    def mock_request_parse(self, mocker):
        return mocker.patch("metagpt.rag.parsers.omniparse.OmniParseClient._request_parse")

    @pytest.mark.asyncio
    async def test_parse_pdf(self, mock_request_parse):
        mock_content = "#test title\ntest content"
        mock_parsed_ret = OmniParsedResult(text=mock_content, markdown=mock_content)
        mock_request_parse.return_value = mock_parsed_ret.model_dump()
        parse_ret = await self.parse_client.parse_pdf(TEST_PDF)
        assert parse_ret == mock_parsed_ret

    @pytest.mark.asyncio
    async def test_parse_document(self, mock_request_parse):
        mock_content = "#test title\ntest_parse_document"
        mock_parsed_ret = OmniParsedResult(text=mock_content, markdown=mock_content)
        mock_request_parse.return_value = mock_parsed_ret.model_dump()

        with open(TEST_DOCX, "rb") as f:
            file_bytes = f.read()

        with pytest.raises(ValueError):
            # bytes data must provide bytes_filename
            await self.parse_client.parse_document(file_bytes)

        parse_ret = await self.parse_client.parse_document(file_bytes, bytes_filename="test.docx")
        assert parse_ret == mock_parsed_ret

    @pytest.mark.asyncio
    async def test_parse_video(self, mock_request_parse):
        mock_content = "#test title\ntest_parse_video"
        mock_request_parse.return_value = {
            "text": mock_content,
            "metadata": {},
        }
        with pytest.raises(ValueError):
            # Wrong file extension test
            await self.parse_client.parse_video(TEST_DOCX)

        parse_ret = await self.parse_client.parse_video(TEST_VIDEO)
        assert "text" in parse_ret and "metadata" in parse_ret
        assert parse_ret["text"] == mock_content

    @pytest.mark.asyncio
    async def test_parse_audio(self, mock_request_parse):
        mock_content = "#test title\ntest_parse_audio"
        mock_request_parse.return_value = {
            "text": mock_content,
            "metadata": {},
        }
        parse_ret = await self.parse_client.parse_audio(TEST_AUDIO)
        assert "text" in parse_ret and "metadata" in parse_ret
        assert parse_ret["text"] == mock_content


class TestOmniParse:
    @pytest.fixture
    def mock_omniparse(self):
        parser = OmniParse(
            parse_options=OmniParseOptions(
                parse_type=OmniParseType.PDF,
                result_type=ParseResultType.MD,
                max_timeout=120,
                num_workers=3,
            )
        )
        return parser

    @pytest.fixture
    def mock_request_parse(self, mocker):
        return mocker.patch("metagpt.rag.parsers.omniparse.OmniParseClient._request_parse")

    @pytest.mark.asyncio
    async def test_load_data(self, mock_omniparse, mock_request_parse):
        # mock
        mock_content = "#test title\ntest content"
        mock_parsed_ret = OmniParsedResult(text=mock_content, markdown=mock_content)
        mock_request_parse.return_value = mock_parsed_ret.model_dump()

        # single file
        documents = mock_omniparse.load_data(file_path=TEST_PDF)
        doc = documents[0]
        assert isinstance(doc, Document)
        assert doc.text == mock_parsed_ret.text == mock_parsed_ret.markdown

        # multi files
        file_paths = [TEST_DOCX, TEST_PDF]
        mock_omniparse.parse_type = OmniParseType.DOCUMENT
        documents = await mock_omniparse.aload_data(file_path=file_paths)
        doc = documents[0]

        # assert
        assert isinstance(doc, Document)
        assert len(documents) == len(file_paths)
        assert doc.text == mock_parsed_ret.text == mock_parsed_ret.markdown

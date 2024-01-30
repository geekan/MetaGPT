from unittest.mock import AsyncMock

import pytest

from metagpt.rag.engines import SimpleEngine


class TestSimpleEngineFromDocs:
    def test_from_docs(self, mocker):
        # Mock dependencies
        mock_simple_directory_reader = mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")
        mock_simple_directory_reader.return_value.load_data.return_value = ["document1", "document2"]

        mock_service_context = mocker.patch("metagpt.rag.engines.simple.ServiceContext.from_defaults")
        mock_vector_store_index = mocker.patch("metagpt.rag.engines.simple.VectorStoreIndex.from_documents")
        mock_vector_index_retriever = mocker.patch("metagpt.rag.engines.simple.VectorIndexRetriever")

        # Setup
        input_dir = "test_dir"
        input_files = ["test_file1", "test_file2"]
        embed_model = mocker.MagicMock()
        llm = mocker.MagicMock()
        chunk_size = 100
        chunk_overlap = 10
        similarity_top_k = 5

        # Execute
        engine = SimpleEngine.from_docs(
            input_dir=input_dir,
            input_files=input_files,
            embed_model=embed_model,
            llm=llm,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_top_k=similarity_top_k,
        )

        # Assertions
        mock_simple_directory_reader.assert_called_once_with(input_dir=input_dir, input_files=input_files)
        mock_service_context.assert_called_once_with(
            embed_model=embed_model, chunk_size=chunk_size, chunk_overlap=chunk_overlap, llm=llm
        )
        mock_vector_store_index.assert_called_once_with(
            ["document1", "document2"], service_context=mock_service_context.return_value
        )
        mock_vector_index_retriever.assert_called_once_with(
            index=mock_vector_store_index.return_value, similarity_top_k=similarity_top_k
        )
        assert isinstance(engine, SimpleEngine)

    @pytest.mark.asyncio
    async def test_asearch_calls_aquery(self, mocker):
        # Mock
        test_query = "test query"
        expected_result = "expected result"
        mock_aquery = AsyncMock(return_value=expected_result)

        # Setup
        engine = SimpleEngine(retriever=mocker.MagicMock())
        engine.aquery = mock_aquery

        # Execute
        result = await engine.asearch(test_query)

        # Assertions
        mock_aquery.assert_called_once_with(test_query)
        assert result == expected_result

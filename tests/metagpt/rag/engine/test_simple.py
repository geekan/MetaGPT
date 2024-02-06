import pytest
from llama_index import VectorStoreIndex

from metagpt.rag.engines import SimpleEngine
from metagpt.rag.retrievers.base import RAGRetriever


class TestSimpleEngine:
    def test_from_docs(self, mocker):
        # Mock
        mock_simple_directory_reader = mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")
        mock_simple_directory_reader.return_value.load_data.return_value = ["document1", "document2"]

        mock_service_context = mocker.patch("metagpt.rag.engines.simple.ServiceContext.from_defaults")
        mock_service_context.return_value = "service_context"

        mock_vector_store_index = mocker.patch("metagpt.rag.engines.simple.VectorStoreIndex.from_documents")
        mock_get_retriever = mocker.patch("metagpt.rag.engines.simple.get_retriever")
        mock_get_rankers = mocker.patch("metagpt.rag.engines.simple.get_rankers")

        # Setup
        input_dir = "test_dir"
        input_files = ["test_file1", "test_file2"]
        embed_model = mocker.MagicMock()
        llm = mocker.MagicMock()
        chunk_size = 100
        chunk_overlap = 10
        retriever_configs = mocker.MagicMock()
        ranker_configs = mocker.MagicMock()

        # Execute
        engine = SimpleEngine.from_docs(
            input_dir=input_dir,
            input_files=input_files,
            embed_model=embed_model,
            llm=llm,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
        )

        # Assertions
        mock_simple_directory_reader.assert_called_once_with(input_dir=input_dir, input_files=input_files)
        mock_service_context.assert_called_once_with(
            embed_model=embed_model, chunk_size=chunk_size, chunk_overlap=chunk_overlap, llm=llm
        )
        mock_vector_store_index.assert_called_once_with(
            ["document1", "document2"], service_context=mock_service_context.return_value
        )
        mock_get_retriever.assert_called_once_with(mock_vector_store_index.return_value, configs=retriever_configs)
        mock_get_rankers.assert_called_once_with(
            configs=ranker_configs, service_context=mock_service_context.return_value
        )

        assert isinstance(engine, SimpleEngine)

    @pytest.mark.asyncio
    async def test_asearch(self, mocker):
        # Mock
        test_query = "test query"
        expected_result = "expected result"
        mock_aquery = mocker.AsyncMock(return_value=expected_result)

        # Setup
        engine = SimpleEngine(retriever=mocker.MagicMock())
        engine.aquery = mock_aquery

        # Execute
        result = await engine.asearch(test_query)

        # Assertions
        mock_aquery.assert_called_once_with(test_query)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_aretrieve(self, mocker):
        # Mock
        mock_query_bundle = mocker.patch("metagpt.rag.engines.simple.QueryBundle", return_value="query_bundle")
        mock_super_aretrieve = mocker.patch(
            "metagpt.rag.engines.simple.RetrieverQueryEngine.aretrieve", new_callable=mocker.AsyncMock
        )
        mock_super_aretrieve.return_value = ["node_with_score"]

        # Setup
        engine = SimpleEngine(retriever=mocker.MagicMock())
        test_query = "test query"

        # Execute
        result = await engine.aretrieve(test_query)

        # Assertions
        mock_query_bundle.assert_called_once_with(test_query)
        mock_super_aretrieve.assert_called_once_with("query_bundle")
        assert result == ["node_with_score"]

    def test_add_docs(self, mocker):
        # Mock
        mock_simple_directory_reader = mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")
        mock_simple_directory_reader.return_value.load_data.return_value = ["document1", "document2"]

        mock_retriever = mocker.MagicMock(spec=RAGRetriever)
        mock_index = mocker.MagicMock(spec=VectorStoreIndex)
        mock_index.service_context.node_parser.get_nodes_from_documents = lambda x: ["node1", "node2"]

        # Setup
        engine = SimpleEngine(retriever=mock_retriever, index=mock_index)
        input_files = ["test_file1", "test_file2"]

        # Execute
        engine.add_docs(input_files=input_files)

        # Assertions
        mock_simple_directory_reader.assert_called_once_with(input_files=input_files)
        mock_retriever.add_nodes.assert_called_once_with(["node1", "node2"])

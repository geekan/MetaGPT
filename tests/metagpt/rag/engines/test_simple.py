import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document, TextNode

from metagpt.rag.engines import SimpleEngine
from metagpt.rag.retrievers.base import ModifiableRAGRetriever


class TestSimpleEngine:
    @pytest.fixture
    def mock_simple_directory_reader(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")

    @pytest.fixture
    def mock_vector_store_index(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.VectorStoreIndex.from_documents")

    @pytest.fixture
    def mock_get_retriever(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.get_retriever")

    @pytest.fixture
    def mock_get_rankers(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.get_rankers")

    @pytest.fixture
    def mock_get_response_synthesizer(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.get_response_synthesizer")

    def test_from_docs(
        self,
        mocker,
        mock_simple_directory_reader,
        mock_vector_store_index,
        mock_get_retriever,
        mock_get_rankers,
        mock_get_response_synthesizer,
    ):
        # Mock
        mock_simple_directory_reader.return_value.load_data.return_value = [
            Document(text="document1"),
            Document(text="document2"),
        ]
        mock_get_retriever.return_value = mocker.MagicMock()
        mock_get_rankers.return_value = [mocker.MagicMock()]
        mock_get_response_synthesizer.return_value = mocker.MagicMock()

        # Setup
        input_dir = "test_dir"
        input_files = ["test_file1", "test_file2"]
        transformations = [mocker.MagicMock()]
        embed_model = mocker.MagicMock()
        llm = mocker.MagicMock()
        retriever_configs = [mocker.MagicMock()]
        ranker_configs = [mocker.MagicMock()]

        # Execute
        engine = SimpleEngine.from_docs(
            input_dir=input_dir,
            input_files=input_files,
            transformations=transformations,
            embed_model=embed_model,
            llm=llm,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
        )

        # Assertions
        mock_simple_directory_reader.assert_called_once_with(input_dir=input_dir, input_files=input_files)
        mock_vector_store_index.assert_called_once()
        mock_get_retriever.assert_called_once_with(
            configs=retriever_configs, index=mock_vector_store_index.return_value
        )
        mock_get_rankers.assert_called_once_with(configs=ranker_configs, llm=llm)
        mock_get_response_synthesizer.assert_called_once_with(llm=llm)
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
        mock_super_aretrieve.return_value = [TextNode(text="node_with_score", metadata={"is_obj": False})]

        # Setup
        engine = SimpleEngine(retriever=mocker.MagicMock())
        test_query = "test query"

        # Execute
        result = await engine.aretrieve(test_query)

        # Assertions
        mock_query_bundle.assert_called_once_with(test_query)
        mock_super_aretrieve.assert_called_once_with("query_bundle")
        assert result[0].text == "node_with_score"

    def test_add_docs(self, mocker):
        # Mock
        mock_simple_directory_reader = mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")
        mock_simple_directory_reader.return_value.load_data.return_value = [
            Document(text="document1"),
            Document(text="document2"),
        ]

        mock_retriever = mocker.MagicMock(spec=ModifiableRAGRetriever)

        mock_index = mocker.MagicMock(spec=VectorStoreIndex)
        mock_index._transformations = mocker.MagicMock()

        mock_run_transformations = mocker.patch("metagpt.rag.engines.simple.run_transformations")
        mock_run_transformations.return_value = ["node1", "node2"]

        # Setup
        engine = SimpleEngine(retriever=mock_retriever, index=mock_index)
        input_files = ["test_file1", "test_file2"]

        # Execute
        engine.add_docs(input_files=input_files)

        # Assertions
        mock_simple_directory_reader.assert_called_once_with(input_files=input_files)
        mock_retriever.add_nodes.assert_called_once_with(["node1", "node2"])

    def test_add_objs(self, mocker):
        # Mock
        mock_retriever = mocker.MagicMock(spec=ModifiableRAGRetriever)

        # Setup
        class CustomTextNode(TextNode):
            def rag_key(self):
                return ""

            def model_dump_json(self):
                return ""

        objs = [CustomTextNode(text=f"text_{i}", metadata={"obj": f"obj_{i}"}) for i in range(2)]
        engine = SimpleEngine(retriever=mock_retriever, index=mocker.MagicMock())

        # Execute
        engine.add_objs(objs=objs)

        # Assertions
        assert mock_retriever.add_nodes.call_count == 1
        for node in mock_retriever.add_nodes.call_args[0][0]:
            assert isinstance(node, TextNode)
            assert "is_obj" in node.metadata

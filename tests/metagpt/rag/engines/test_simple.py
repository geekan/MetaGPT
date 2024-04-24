import json

import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.schema import Document, NodeWithScore, TextNode

from metagpt.rag.engines import SimpleEngine
from metagpt.rag.retrievers import SimpleHybridRetriever
from metagpt.rag.retrievers.base import ModifiableRAGRetriever, PersistableRAGRetriever
from metagpt.rag.schema import BM25RetrieverConfig, ObjectNode


class TestSimpleEngine:
    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def mock_embedding(self):
        return MockEmbedding(embed_dim=1)

    @pytest.fixture
    def mock_simple_directory_reader(self, mocker):
        return mocker.patch("metagpt.rag.engines.simple.SimpleDirectoryReader")

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

        # Exec
        engine = SimpleEngine.from_docs(
            input_dir=input_dir,
            input_files=input_files,
            transformations=transformations,
            embed_model=embed_model,
            llm=llm,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
        )

        # Assert
        mock_simple_directory_reader.assert_called_once_with(input_dir=input_dir, input_files=input_files)
        mock_get_retriever.assert_called_once()
        mock_get_rankers.assert_called_once()
        mock_get_response_synthesizer.assert_called_once_with(llm=llm)
        assert isinstance(engine, SimpleEngine)

    def test_from_docs_without_file(self):
        with pytest.raises(ValueError):
            SimpleEngine.from_docs()

    def test_from_objs(self, mock_llm, mock_embedding):
        # Mock
        class MockRAGObject:
            def rag_key(self):
                return "key"

            def model_dump_json(self):
                return "{}"

        objs = [MockRAGObject()]

        # Setup
        retriever_configs = []
        ranker_configs = []

        # Exec
        engine = SimpleEngine.from_objs(
            objs=objs,
            llm=mock_llm,
            embed_model=mock_embedding,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
        )

        # Assert
        assert isinstance(engine, SimpleEngine)
        assert engine._transformations is not None

    def test_from_objs_with_bm25_config(self):
        # Setup
        retriever_configs = [BM25RetrieverConfig()]

        # Exec
        with pytest.raises(ValueError):
            SimpleEngine.from_objs(
                objs=[],
                llm=MockLLM(),
                retriever_configs=retriever_configs,
                ranker_configs=[],
            )

    def test_from_index(self, mocker, mock_llm, mock_embedding):
        # Mock
        mock_index = mocker.MagicMock(spec=VectorStoreIndex)
        mock_index.as_retriever.return_value = "retriever"
        mock_get_index = mocker.patch("metagpt.rag.engines.simple.get_index")
        mock_get_index.return_value = mock_index

        # Exec
        engine = SimpleEngine.from_index(
            index_config=mock_index,
            embed_model=mock_embedding,
            llm=mock_llm,
        )

        # Assert
        assert isinstance(engine, SimpleEngine)
        assert engine._retriever == "retriever"

    @pytest.mark.asyncio
    async def test_asearch(self, mocker):
        # Mock
        test_query = "test query"
        expected_result = "expected result"
        mock_aquery = mocker.AsyncMock(return_value=expected_result)

        # Setup
        engine = SimpleEngine(retriever=mocker.MagicMock())
        engine.aquery = mock_aquery

        # Exec
        result = await engine.asearch(test_query)

        # Assert
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

        # Exec
        result = await engine.aretrieve(test_query)

        # Assert
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

        mock_run_transformations = mocker.patch("metagpt.rag.engines.simple.run_transformations")
        mock_run_transformations.return_value = ["node1", "node2"]

        # Setup
        engine = SimpleEngine(retriever=mock_retriever)
        input_files = ["test_file1", "test_file2"]

        # Exec
        engine.add_docs(input_files=input_files)

        # Assert
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
        engine = SimpleEngine(retriever=mock_retriever)

        # Exec
        engine.add_objs(objs=objs)

        # Assert
        assert mock_retriever.add_nodes.call_count == 1
        for node in mock_retriever.add_nodes.call_args[0][0]:
            assert isinstance(node, TextNode)
            assert "is_obj" in node.metadata

    def test_persist_successfully(self, mocker):
        # Mock
        mock_retriever = mocker.MagicMock(spec=PersistableRAGRetriever)
        mock_retriever.persist.return_value = mocker.MagicMock()

        # Setup
        engine = SimpleEngine(retriever=mock_retriever)

        # Exec
        engine.persist(persist_dir="")

    def test_ensure_retriever_of_type(self, mocker):
        # Mock
        class MyRetriever:
            def add_nodes(self):
                ...

        mock_retriever = mocker.MagicMock(spec=SimpleHybridRetriever)
        mock_retriever.retrievers = [MyRetriever()]

        # Setup
        engine = SimpleEngine(retriever=mock_retriever)

        # Assert
        engine._ensure_retriever_of_type(ModifiableRAGRetriever)

        with pytest.raises(TypeError):
            engine._ensure_retriever_of_type(PersistableRAGRetriever)

        with pytest.raises(TypeError):
            other_engine = SimpleEngine(retriever=mocker.MagicMock(spec=ModifiableRAGRetriever))
            other_engine._ensure_retriever_of_type(PersistableRAGRetriever)

    def test_with_obj_metadata(self, mocker):
        # Mock
        node = NodeWithScore(
            node=ObjectNode(
                text="example",
                metadata={
                    "is_obj": True,
                    "obj_cls_name": "ExampleObject",
                    "obj_mod_name": "__main__",
                    "obj_json": json.dumps({"key": "test_key", "value": "test_value"}),
                },
            )
        )

        class ExampleObject:
            def __init__(self, key, value):
                self.key = key
                self.value = value

            def __eq__(self, other):
                return self.key == other.key and self.value == other.value

        mock_import_class = mocker.patch("metagpt.rag.engines.simple.import_class")
        mock_import_class.return_value = ExampleObject

        # Setup
        SimpleEngine._try_reconstruct_obj([node])

        # Exec
        expected_obj = ExampleObject(key="test_key", value="test_value")

        # Assert
        assert "obj" in node.node.metadata
        assert node.node.metadata["obj"] == expected_obj

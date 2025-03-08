import json
from typing import Any, List, Optional

from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.evaluation.benchmarks import HotpotQAEvaluator
from llama_index.core.evaluation.benchmarks.hotpotqa import exact_match_score, f1_score
from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.query_analysis.hyde import HyDEQuery
from metagpt.rag.query_analysis.simple_query_transformer import SimpleQueryTransformer
from metagpt.rag.schema import FAISSRetrieverConfig


class HotpotQA(HotpotQAEvaluator):
    def run(
        self,
        query_engine: BaseQueryEngine,
        queries: int = 10,
        queries_fraction: Optional[float] = None,
        show_result: bool = False,
        hyde: bool = False,
    ) -> None:
        dataset_paths = self._download_datasets()
        dataset = "hotpot_dev_distractor"
        dataset_path = dataset_paths[dataset]
        print("Evaluating on dataset:", dataset)
        print("-------------------------------------")

        f = open(dataset_path)
        query_objects = json.loads(f.read())
        if queries_fraction:
            queries_to_load = int(len(query_objects) * queries_fraction)
        else:
            queries_to_load = queries
            queries_fraction = round(queries / len(query_objects), 5)

        print(
            f"Loading {queries_to_load} queries out of \
    {len(query_objects)} (fraction: {queries_fraction})"
        )
        query_objects = query_objects[:queries_to_load]

        assert isinstance(
            query_engine, RetrieverQueryEngine
        ), "query_engine must be a RetrieverQueryEngine for this evaluation"
        retriever = HotpotQARetriever(query_objects, hyde)
        # Mock the query engine with a retriever
        query_engine = query_engine.with_retriever(retriever=retriever)
        if hyde:
            hyde_query = HyDEQuery()
            query_engine = SimpleQueryTransformer(query_engine, hyde_query)
        scores = {"exact_match": 0.0, "f1": 0.0}

        for query in query_objects:
            if hyde:
                response = query_engine.query(
                    query["question"] + " Give a short factoid answer (as few words as possible)."
                )
            else:
                query_bundle = QueryBundle(
                    query_str=query["question"] + " Give a short factoid answer (as few words as possible).",
                    custom_embedding_strs=[query["question"]],
                )
                response = query_engine.query(query_bundle)
            em = int(exact_match_score(prediction=str(response), ground_truth=query["answer"]))
            f1, _, _ = f1_score(prediction=str(response), ground_truth=query["answer"])
            scores["exact_match"] += em
            scores["f1"] += f1
            if show_result:
                print("Question: ", query["question"])
                print("Response:", response)
                print("Correct answer: ", query["answer"])
                print("EM:", em, "F1:", f1)
                print("-------------------------------------")

        for score in scores:
            scores[score] /= len(query_objects)

        print("Scores: ", scores)


class HotpotQARetriever(BaseRetriever):
    """
    This is a mocked retriever for HotpotQA dataset. It is only meant to be used
    with the hotpotqa dev dataset in the distractor setting. This is the setting that
    does not require retrieval but requires identifying the supporting facts from
    a list of 10 sources.
    """

    def __init__(self, query_objects: Any, hyde: bool) -> None:
        self.hyde = hyde
        assert isinstance(
            query_objects,
            list,
        ), f"query_objects must be a list, got: {type(query_objects)}"
        self._queries = {}
        for object in query_objects:
            self._queries[object["question"]] = object

    def _retrieve(self, query: QueryBundle) -> List[NodeWithScore]:
        if query.custom_embedding_strs and self.hyde is False:
            query_str = query.custom_embedding_strs[0]
        else:
            query_str = query.query_str.replace(" Give a short factoid answer (as few words as possible).", "")
        contexts = self._queries[query_str]["context"]
        node_with_scores = []
        for ctx in contexts:
            text_list = ctx[1]
            text = "\n".join(text_list)
            node = TextNode(text=text, metadata={"title": ctx[0]})
            node_with_scores.append(NodeWithScore(node=node, score=1.0))

        return node_with_scores

    def __str__(self) -> str:
        return "HotpotQARetriever"


if __name__ == "__main__":
    DOC_PATH = EXAMPLE_DATA_PATH / "rag/writer.txt"
    engine = SimpleEngine.from_docs(input_files=[DOC_PATH], retriever_configs=[FAISSRetrieverConfig()])
    HotpotQA().run(engine, queries=100, show_result=True, hyde=True)
    HotpotQA().run(engine, queries=100, show_result=True, hyde=False)

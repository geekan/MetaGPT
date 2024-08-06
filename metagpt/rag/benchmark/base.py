import asyncio
from typing import List, Tuple, Union

import evaluate
import jieba
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.evaluation import SemanticSimilarityEvaluator
from llama_index.core.schema import NodeWithScore
from pydantic import BaseModel

from metagpt.const import EXAMPLE_BENCHMARK_PATH
from metagpt.logs import logger
from metagpt.rag.factories import get_rag_embedding
from metagpt.utils.common import read_json_file


class DatasetInfo(BaseModel):
    name: str
    document_files: List[str]
    gt_info: List[dict]


class DatasetConfig(BaseModel):
    datasets: List[DatasetInfo]


class RAGBenchmark:
    def __init__(
        self,
        embed_model: BaseEmbedding = None,
    ):
        self.evaluator = SemanticSimilarityEvaluator(
            embed_model=embed_model or get_rag_embedding(),
        )

    def set_metrics(
        self,
        bleu_avg: float = 0.0,
        bleu_1: float = 0.0,
        bleu_2: float = 0.0,
        bleu_3: float = 0.0,
        bleu_4: float = 0.0,
        rouge_l: float = 0.0,
        semantic_similarity: float = 0.0,
        recall: float = 0.0,
        hit_rate: float = 0.0,
        mrr: float = 0.0,
        length: float = 0.0,
        generated_text: str = None,
        ground_truth_text: str = None,
        question: str = None,
    ):
        metrics = {
            "bleu-avg": bleu_avg,
            "bleu-1": bleu_1,
            "bleu-2": bleu_2,
            "bleu-3": bleu_3,
            "bleu-4": bleu_4,
            "rouge-L": rouge_l,
            "semantic similarity": semantic_similarity,
            "recall": recall,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "length": length,
        }

        log = {
            "generated_text": generated_text,
            "ground_truth_text": ground_truth_text,
            "question": question,
        }

        return {"metrics": metrics, "log": log}

    def bleu_score(self, response: str, reference: str, with_penalty=False) -> Union[float, Tuple[float]]:
        f = lambda text: list(jieba.cut(text))
        bleu = evaluate.load(path="bleu")
        results = bleu.compute(predictions=[response], references=[[reference]], tokenizer=f)

        bleu_avg = results["bleu"]
        bleu1 = results["precisions"][0]
        bleu2 = results["precisions"][1]
        bleu3 = results["precisions"][2]
        bleu4 = results["precisions"][3]
        brevity_penalty = results["brevity_penalty"]

        if with_penalty:
            return bleu_avg, bleu1, bleu2, bleu3, bleu4
        else:
            return 0.0 if brevity_penalty == 0 else bleu_avg / brevity_penalty, bleu1, bleu2, bleu3, bleu4

    def rougel_score(self, response: str, reference: str) -> float:
        # pip install rouge_score
        f = lambda text: list(jieba.cut(text))
        rouge = evaluate.load(path="rouge")

        results = rouge.compute(predictions=[response], references=[[reference]], tokenizer=f, rouge_types=["rougeL"])
        score = results["rougeL"]
        return score

    def recall(self, nodes: list[NodeWithScore], reference_docs: list[str]) -> float:
        if nodes:
            total_recall = sum(any(node.text in doc for node in nodes) for doc in reference_docs)
            return total_recall / len(reference_docs)
        else:
            return 0.0

    def hit_rate(self, nodes: list[NodeWithScore], reference_docs: list[str]) -> float:
        if nodes:
            return 1.0 if any(node.text in doc for doc in reference_docs for node in nodes) else 0.0
        else:
            return 0.0

    def mean_reciprocal_rank(self, nodes: list[NodeWithScore], reference_docs: list[str]) -> float:
        mrr_sum = 0.0

        for i, node in enumerate(nodes, start=1):
            for doc in reference_docs:
                if text in doc:
                    mrr_sum += 1.0 / i
                    return mrr_sum

        return mrr_sum

    async def semantic_similarity(self, response: str, reference: str) -> float:
        result = await self.evaluator.aevaluate(
            response=response,
            reference=reference,
        )

        return result.score

    async def compute_metric(
        self,
        response: str = None,
        reference: str = None,
        nodes: list[NodeWithScore] = None,
        reference_doc: list[str] = None,
        question: str = None,
    ):
        recall = self.recall(nodes, reference_doc)
        bleu_avg, bleu1, bleu2, bleu3, bleu4 = self.bleu_score(response, reference)
        rouge_l = self.rougel_score(response, reference)
        hit_rate = self.hit_rate(nodes, reference_doc)
        mrr = self.mean_reciprocal_rank(nodes, reference_doc)

        similarity = await self.semantic_similarity(response, reference)

        result = self.set_metrics(
            bleu_avg,
            bleu1,
            bleu2,
            bleu3,
            bleu4,
            rouge_l,
            similarity,
            recall,
            hit_rate,
            mrr,
            len(response),
            response,
            reference,
            question,
        )

        return result

    @staticmethod
    def load_dataset(ds_names: list[str] = ["all"]):
        infos = read_json_file((EXAMPLE_BENCHMARK_PATH / "dataset_info.json").as_posix())
        dataset_config = DatasetConfig(
            datasets=[
                DatasetInfo(
                    name=name,
                    document_files=[
                        (EXAMPLE_BENCHMARK_PATH / name / file).as_posix() for file in info["document_file"]
                    ],
                    gt_info=read_json_file((EXAMPLE_BENCHMARK_PATH / name / info["gt_file"]).as_posix()),
                )
                for dataset_info in infos
                for name, info in dataset_info.items()
                if name in ds_names or "all" in ds_names
            ]
        )

        return dataset_config


if __name__ == "__main__":
    benchmark = RAGBenchmark()
    answer = "是的，根据提供的信息，2023年7月20日，应急管理部和财政部确实联合发布了《因灾倒塌、损坏住房恢复重建救助工作规范》的通知。这份《规范》旨在进一步规范因灾倒塌、损坏住房的恢复重建救助相关工作。它明确了地方各级政府负责实施救助工作，应急管理部和财政部则负责统筹指导。地方财政应安排足够的资金，中央财政也会提供适当的补助。救助资金将通过专账管理，并采取特定的管理方式。救助对象是那些因自然灾害导致住房倒塌或损坏，并向政府提出申请且符合条件的受灾家庭。相关部门将组织调查统计救助对象信息，并建立档案。此外，《规范》还强调了资金发放的具体方式和公开透明的要求。"
    ground_truth = "“启明行动”是为了防控儿童青少年的近视问题，并发布了《防控儿童青少年近视核心知识十条》。"
    bleu_avg, bleu1, bleu2, bleu3, bleu4 = benchmark.bleu_score(answer, ground_truth)
    rougeL_score = benchmark.rougel_score(answer, ground_truth)
    similarity = asyncio.run(benchmark.SemanticSimilarity(answer, ground_truth))

    logger.info(
        f"BLEU Scores: bleu_avg = {bleu_avg}, bleu1 = {bleu1}, bleu2 = {bleu2}, bleu3 = {bleu3}, bleu4 = {bleu4}, "
        f"RougeL Score: {rougeL_score}, "
        f"Semantic Similarity: {similarity}"
    )

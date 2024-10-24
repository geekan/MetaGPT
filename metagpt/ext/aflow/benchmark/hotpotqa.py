import re
import string
from collections import Counter
from typing import Callable, List, Tuple

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from metagpt.ext.aflow.benchmark.benchmark import BaseBenchmark
from metagpt.logs import logger


class HotpotQABenchmark(BaseBenchmark):
    def __init__(self, name: str, file_path: str, log_path: str):
        super().__init__(name, file_path, log_path)

    def normalize_answer(self, s: str) -> str:
        def remove_articles(text):
            return re.sub(r"\b(a|an|the)\b", " ", text)

        def white_space_fix(text):
            return " ".join(text.split())

        def remove_punc(text):
            exclude = set(string.punctuation)
            return "".join(ch for ch in text if ch not in exclude)

        def lower(text):
            return text.lower()

        return white_space_fix(remove_articles(remove_punc(lower(s))))

    def calculate_score(self, ground_truth: str, prediction: str) -> Tuple[float, str]:
        prediction_tokens = self.normalize_answer(prediction).split()
        ground_truth_tokens = self.normalize_answer(ground_truth).split()
        common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
        num_same = sum(common.values())
        if num_same == 0:
            return 0, prediction
        precision = 1.0 * num_same / len(prediction_tokens)
        recall = 1.0 * num_same / len(ground_truth_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        return f1, prediction

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1), retry=retry_if_exception_type(Exception), reraise=True)
    async def _generate_output(self, graph, input_text):
        return await graph(input_text)

    async def evaluate_problem(self, problem: dict, graph: Callable) -> Tuple[str, str, str, str, float, float]:
        input_text = problem["question"]
        expected_output = problem["answer"]
        paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
        context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
        inputs = f"Context: {context_str}\n\nQuestion: {input_text}\n\nAnswer:"

        try:
            output, cost = await self._generate_output(graph, inputs)
            score, extracted_output = self.calculate_score(expected_output, output)

            if (
                score < 0.3
            ):  # We set the threshold for collecting incorrect questions to 0.3, as F1 Score cannot be simply judged using 0-1
                self.log_mismatch(input_text, expected_output, output, extracted_output)

            return input_text, context_str, output, expected_output, score, cost

        except Exception as e:
            logger.info(f"Maximum retries reached. Skipping this sample. Error: {e}")
            return input_text, context_str, str(e), expected_output, 0.0, 0.0

    def get_result_columns(self) -> List[str]:
        return ["question", "context", "prediction", "expected_output", "score", "cost"]

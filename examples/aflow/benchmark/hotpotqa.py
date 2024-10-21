import json
import asyncio
import aiofiles
import pandas as pd
from typing import List, Tuple, Callable, Any
import string
import re
import os
from collections import Counter

from examples.aflow.benchmark.benchmark import BaseBenchmark

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

    async def evaluate_problem(self, problem: dict, graph: Callable) -> Tuple[str, str, str, str, float, float]:
        input_text = problem["question"]
        expected_output = problem["answer"]
        paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
        context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
        inputs = f"Context: {context_str}\n\nQuestion: {input_text}\n\nAnswer:"

        max_retries = 5
        retries = 0

        while retries < max_retries:
            try:
                output, cost = await graph(inputs)
                score, _ = self.calculate_score(expected_output, output)

                if score < 0.3:
                    self.log_mismatch(input_text, expected_output, output, output)

                return input_text, context_str, output, expected_output, score, cost

            except Exception as e:
                retries += 1
                print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                if retries == max_retries:
                    print("Maximum retries reached. Skipping this sample.")
                    return input_text, context_str, str(e), expected_output, 0.0, 0.0

    def get_result_columns(self) -> List[str]:
        return ["question", "context", "prediction", "expected_output", "score", "cost"]

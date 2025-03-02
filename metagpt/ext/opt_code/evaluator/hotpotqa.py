from metagpt.ext.opt_code.memory.base_memory import CodeNode
from metagpt.ext.opt_code.evaluator.base_evaluator import Evaluator
import numpy as np
from typing import Tuple
from collections import Counter
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import time
import os
import string
import json
import re

class HotpotQAEvaluator(Evaluator):
    def __init__(self, train_data_path: str, test_data_path: str, llm_config):
        super().__init__(train_data_path, test_data_path, llm_config)

    def load_data(self, path):
        data = []
        with open(path, "r") as f:
            for line in f:
                data.append(json.loads(line))

        return data

    # def random_sample(self, data, k, seed=42):
    #     np.random.seed(seed)
    #     return np.random.choice(data, k)

    async def _evaluate(self, executor, data):
        def normalize_answer(s: str) -> str:
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
        
        def calculate_score(ground_truth: str, prediction: str) -> Tuple[float, str]:
            prediction_tokens = normalize_answer(prediction).split()
            ground_truth_tokens = normalize_answer(ground_truth).split()
            common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                return 0, prediction
            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(ground_truth_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            return f1, prediction

        @retry(stop=stop_after_attempt(5), wait=wait_fixed(1), retry=retry_if_exception_type(Exception), reraise=True)
        async def _generate(executor, input):
            return await executor(input)
        
        result = []
        for d in data:
            input_text = d["question"]
            expected_output = d["answer"]
            paragraphs = [item[1] for item in d["context"] if isinstance(item[1], list)]
            context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
            inputs = f"Context: {context_str}\n\nQuestion: {input_text}\n\nAnswer:"

            try:
                output, cost = await _generate(executor, inputs)
                score, extracted_output = calculate_score(expected_output, output)
            except Exception as e:
                score = 0
                extracted_output = "Error"
                cost = 0

            result.append({"Question": d["question"], "Expected Answer": d["answer"], "Predicted Answer": extracted_output, "Score": score, "Cost": cost})

        avg_score = np.mean([item["Score"] for item in result])

        return avg_score, result

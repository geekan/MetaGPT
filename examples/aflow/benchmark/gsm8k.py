# -*- coding: utf-8 -*-
# @Date    :
# @Author  : all
# @Desc    : test on gsm8k
import re
import json
import asyncio
import aiofiles
import pandas as pd
from typing import Optional, List, Tuple, Callable, Any

from pandas import Series
from tqdm.asyncio import tqdm_asyncio
import os
import time
from datetime import datetime

from examples.aflow.benchmark.benchmark import BaseBenchmark

class GSM8KBenchmark(BaseBenchmark):
    def __init__(self, name: str, file_path: str, log_path: str):
        super().__init__(name, file_path, log_path)

    def extract_number(self, text: str) -> Optional[float]:
        matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", str(text))
        if matches:
            last_number = matches[-1].replace(",", "")
            try:
                return float(last_number)
            except ValueError:
                return None
        else:
            return None

    def calculate_score(self, expected_output: float, prediction: float) -> Tuple[float, float]:
        if prediction is None:
            return 0.0, prediction
        return 1.0 if abs(expected_output - prediction) <= 1e-6 else 0.0, prediction

    async def evaluate_problem(self, problem: dict, graph: Callable) -> Tuple[str, str, float, float, float]:
        max_retries = 5
        retries = 0
    
        while retries < max_retries:
            try:
                prediction, cost = await graph(problem["question"])
                predicted_number = self.extract_number(prediction)
                expected_output = self.extract_number(problem["answer"])

                score, _ = self.calculate_score(expected_output, predicted_number)

                if score == 0:
                    self.log_mismatch(problem["question"], expected_output, prediction, predicted_number)

                return problem["question"], prediction, expected_output, score, cost

            except Exception as e:
                retries += 1
                print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                if retries == max_retries:
                    print("Maximum retries reached. Skipping this sample.")
                    return problem["question"], str(e), self.extract_number(problem["answer"]), 0.0, 0.0

    def get_result_columns(self) -> List[str]:
        return ["question", "prediction", "expected_output", "score", "cost"]

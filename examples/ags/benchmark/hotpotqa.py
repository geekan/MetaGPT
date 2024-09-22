import json
import asyncio
import aiofiles
import pandas as pd
import numpy as np
from typing import List, Tuple, Callable, Set
from collections import Counter
from tqdm.asyncio import tqdm_asyncio
from scipy.optimize import linear_sum_assignment
import string
import re


from examples.ags.benchmark.utils import generate_random_indices

global cost
cost = 0

def is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False

def normalize_answer(s):
    """
    Normalize answers for evaluation.
    """

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

def f1_score(prediction, ground_truth):
    """
    Compute the F1 score between prediction and ground truth answers.
    """
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


async def load_data(file_path: str, samples=20, total_length=1250, test=False) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), total_length, False) # get random indices of 1250
    random_indices = random_indices[:samples] if not test else random_indices[samples:] # get n_samples for validation or test
    data = [data[i] for i in random_indices]
    return data

async def evaluate_problem(input: str, context_str: str, graph: Callable, expected_output: str):
    max_retries = 5
    retries = 0

    # global cost
    # prediction, cost = await graph(input, context_str) if graph else "None"
    # score = f1_score(prediction, expected_output)

    while retries < max_retries:
        try:
            global cost
            prediction, cost = await graph(input, context_str) if graph else "None"
            score = f1_score(prediction, expected_output)

            break
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                prediction = None
                score = 0
                break

    return input, prediction, expected_output, score

async def evaluate_all_problems(data: List[dict], graph: Callable, max_concurrent_tasks: int = 50):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            input_text = problem["question"]
            expected_output = problem["answer"]
            paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
            context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
            return await evaluate_problem(input_text, context_str, graph, expected_output)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating HotpotQA problems", total=len(data))

def save_results_to_csv(results: List[Tuple[str, str, str, float]], path: str) -> float:
    df = pd.DataFrame(
        results, columns=["question", "prediction", "expected_output", "score"]
    )
    average_score = df["score"].mean()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return average_score

async def hotpotqa_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> float:
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on HotpotQA dataset: {average_score:.5f}")
    global cost
    print(f"Total cost: {cost: .5f}")
    print(f"Cost per sample: {(cost / len(data)):.9f}")
    return average_score

async def load_file_data(file_path: str) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    return data

async def optimize_hotpotqa_evaluation(graph: Callable, file_path: str, path: str) -> Tuple[float, float]:
    data = await load_file_data(file_path)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=50)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on HotpotQA dataset: {average_score:.5f}")
    global cost
    print(f"Total cost: {cost: .5f}")
    print(f"Cost per sample: {(cost / len(data)):.9f}")
    return average_score, cost
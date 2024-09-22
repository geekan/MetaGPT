import json
import asyncio
import pandas as pd
import string
import re
from typing import List, Tuple, Callable, Dict, Any, Set, Union
from collections import Counter
import numpy as np
from scipy.optimize import linear_sum_assignment
from tqdm.asyncio import tqdm_asyncio

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

def compute_f1_score(prediction, ground_truth):
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

# def fuzzy_match(s1: str, s2: str) -> bool:
#     s1 = normalize(s1)
#     s2 = normalize(s2)

#     if s1 == "" or s2 == "":
#         return s1 == s2

#     return s1 in s2 or s2 in s1


# def drop_metric(sample: str, reference: list[str]) -> Tuple[float, float]:
#     em_scores = []
#     f1_scores = []
#     for answer in reference:
#         if answer.strip() != "":
#             em, f1 = get_drop_metrics(sample, answer)
#             em_scores.append(em)
#             f1_scores.append(f1)
#     return (max(em_scores), max(f1_scores))

async def evaluate_problem(inputs: str, answers: List[Dict[str, Any]], graph: Callable) -> Tuple[str, str, float]:

    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            global cost
            prediction, cost = await graph(inputs)

            f1_scores = []

            for answer in answers:
                if answer.strip() != "":
                    f1_score = compute_f1_score(prediction, answer)
                    f1_scores.append(f1_score)

            max_score = max(f1_scores)

            # matches = [
            #         fuzzy_match(prediction, answer)
            #         for answer in answers
            # ]

            # score = True in matches

            score = max_score

            break

        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                prediction = None
                score = 0.0
                break

    return prediction, score

async def evaluate_all_questions(annotations: List[Tuple[str, Dict[str, Any]]], graph: Callable, max_concurrent_tasks: int = 50) -> List[List[Any]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    results = []

    async def sem_evaluate(annotation: Dict[str, Any]):
        async with semaphore:
            inputs = annotation["context"]
            answers = annotation["targets"]
            prediction, score = await evaluate_problem(inputs, answers, graph)
            results.append([annotation["id"], prediction, answers, score])

    tasks = [sem_evaluate(annotation) for annotation in annotations]
    await tqdm_asyncio.gather(*tasks, desc="Evaluating DROP passages", total=len(annotations))

    return results

def save_results_to_csv(results: List[List[Any]], path: str) -> float:
    df = pd.DataFrame(results, columns=["id", "prediction", "answers", "score"])
    average_score = df["score"].mean()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return average_score

# -- From ADAS --

def load_drop(file_path, samples, test=False, total_length=1000):
    import gzip
    with gzip.open(file_path, "rb") as file:
        data = [json.loads(line) for line in file]

    random_indices = generate_random_indices(len(data), total_length, False)
    random_indices = random_indices[:samples] if not test else random_indices[samples:]
    examples = [data[i] for i in random_indices]

    for example in examples:
        example["targets"] = example["ref_text"].split("|")    

    return examples

async def drop_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> float:
    # data = load_data(file_path, samples, test=test)
    data = load_drop(file_path, samples, test=test)
    results = await evaluate_all_questions(data, graph, max_concurrent_tasks=30)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on DROP dataset: {average_score:.5f}")
    global cost
    print(f"Total cost: {cost: .5f}")
    print(f"Cost per sample: {(cost / len(data)):.9f}")
    return average_score, cost

def load_drop_from_file(file_path):
    import gzip
    with gzip.open(file_path, "rb") as file:
        data = [json.loads(line) for line in file]

    for example in data:
        example["targets"] = example["ref_text"].split("|")    

    return data

async def optimize_hotpotqa_evaluation(graph: Callable, file_path: str, path: str) -> Tuple[float, float]:
    data = await load_drop_from_file(file_path)
    results = await evaluate_all_questions(data, graph, max_concurrent_tasks=50)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on DROP dataset: {average_score:.5f}")
    global cost
    print(f"Total cost: {cost: .5f}")
    print(f"Cost per sample: {(cost / len(data)):.9f}")
    return average_score, cost
import json
import asyncio
import aiofiles
import pandas as pd
import numpy as np
from typing import List, Tuple, Callable, Set
from tqdm.asyncio import tqdm_asyncio
from scipy.optimize import linear_sum_assignment

from examples.ags.benchmark.utils import generate_random_indices

def is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False

def normalize_answer(text):
    import re
    import string

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    def tokenize(text):
        return re.split(" |-", text)

    def normalize_number(text: str) -> str:
        if is_number(text):
            return str(float(text))
        else:
            return text

    parts = [
        white_space_fix(remove_articles(normalize_number(remove_punc(lower(token)))))
        for token in tokenize(text)
    ]
    parts = [part for part in parts if part.strip()]
    normalized = " ".join(parts).strip()
    return normalized

def answer_to_bags(answer: str) -> Set[str]:
    raw_spans = [answer]

    normalized_spans = []
    token_bags = []
    for raw_span in raw_spans:
        normalized_span = normalize_answer(raw_span)
        normalized_spans.append(normalized_span)
        token_bags.append(set(normalized_span.split()))
    return normalized_spans, token_bags

def _align_bags(predicted: List[Set[str]], gold: List[Set[str]]) -> List[float]:
    """
    Takes gold and predicted answer sets and first finds the optimal 1-1 alignment
    between them and gets maximum metric values over all the answers.
    """
    scores = np.zeros([len(gold), len(predicted)])
    for gold_index, gold_item in enumerate(gold):
        for pred_index, pred_item in enumerate(predicted):
            if match_numbers_if_present(gold_item, pred_item):
                scores[gold_index, pred_index] = f1_score(pred_item, gold_item)
    row_ind, col_ind = linear_sum_assignment(-scores)

    max_scores = np.zeros([max(len(gold), len(predicted))])
    for row, column in zip(row_ind, col_ind):
        max_scores[row] = max(max_scores[row], scores[row, column])
    return max_scores

def match_numbers_if_present(gold_bag: Set[str], predicted_bag: Set[str]) -> bool:
    gold_numbers = set()
    predicted_numbers = set()
    for word in gold_bag:
        if is_number(word):
            gold_numbers.add(word)
    for word in predicted_bag:
        if is_number(word):
            predicted_numbers.add(word)
    if (not gold_numbers) or gold_numbers.intersection(predicted_numbers):
        return True
    return False

def f1_score(predicted_bag: Set[str], gold_bag: Set[str]) -> float:
    intersection = len(gold_bag.intersection(predicted_bag))
    if not predicted_bag:
        precision = 1.0
    else:
        precision = intersection / float(len(predicted_bag))
    if not gold_bag:
        recall = 1.0
    else:
        recall = intersection / float(len(gold_bag))
    f1 = (2 * precision * recall) / (precision + recall) if not (precision == 0.0 and recall == 0.0) else 0.0
    return f1

async def load_data(file_path: str, samples=20, total_length=1000) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    data = data[:total_length] 
    random_indices = generate_random_indices(len(data), samples)
    data = [data[i] for i in random_indices]
    return data

async def evaluate_problem(input: str, context_str: str, graph: Callable, expected_output: str):
    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            prediction, supporting_sentences = await graph(input, context_str) if graph else "None"
            predicted_bags = answer_to_bags(prediction)
            gold_bags = answer_to_bags(expected_output)

            f1_per_bag = _align_bags(predicted_bags[1], gold_bags[1])
            score = np.mean(f1_per_bag)

            break
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                prediction = None
                supporting_sentences = None
                score = 0
                break

    return input, prediction, expected_output, supporting_sentences, score

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

def save_results_to_csv(results: List[Tuple[str, str, str, str, float]], path: str) -> float:
    df = pd.DataFrame(
        results, columns=["question", "prediction", "expected_output", "supporting_sentences", "score"]
    )
    average_score = df["score"].mean()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return average_score

async def hotpotqa_evaluation(graph: Callable, file_path: str, samples: int, path: str) -> float:
    data = await load_data(file_path, samples)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on HotpotQA dataset: {average_score:.5f}")
    return average_score

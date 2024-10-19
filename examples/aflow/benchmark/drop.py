import os
import re
import json
import asyncio
import string
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple

import aiofiles
import pandas as pd
from tqdm.asyncio import tqdm_asyncio


def is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False

def normalize_answer(s: str) -> List[str]:
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

def calculate_score(ground_truth: str, prediction: str) -> Tuple[float, str]:
    """
    Compute the F1 score between prediction and ground truth answers.
    """
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

def ensure_log_file_exists(path: str):
    log_file = os.path.join(path, 'log.json')
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)


def log_mismatch(problem: str, expected_output, prediction: str, predicted_number, path):
    log_data = {
        "question": problem,
        "right_answer": expected_output,
        "model_output": prediction,
        "extracted_output": predicted_number
    }

    log_file = os.path.join(path, 'log.json')

    # Check if the log file already exists
    if os.path.exists(log_file):
        # If it exists, load the existing log data
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        # If it doesn't exist, create an empty list
        data = []

    # Add the new log data to the existing list
    data.append(log_data)

    # Write the updated list back to the log file
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def load_data(file_path: str, specific_indices: List[int] = None) -> List[dict]:
    data = []
    # Read the data from the file
    async with aiofiles.open(file_path, mode="r", encoding='utf-8') as file:
        async for line in file:
            data.append(json.loads(line))

    # Then further filter based on a specific index list in randomly selected samples
    if specific_indices is not None:
        filtered_data = [data[i] for i in specific_indices if i < len(data)]
        return filtered_data

    return data

def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
    # Create a DataFrame from the results
    df = pd.DataFrame(results, columns=["inputs", "prediction", "expected_output", "score", "cost"])

    # Calculate the average score and cost
    avg_score = df["score"].mean()
    t_cost = df["cost"].max()
    a_cost = t_cost / len(df) if len(df) > 0 else 0

    # Get the current time in the format YYYYMMDD_HHMMSS
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate a filename with the average score and the current time, rounded to five decimal places
    filename = f"{avg_score:.5f}_{current_time}.csv"
    output_file = os.path.join(path, filename)

    # Save the DataFrame to a CSV file
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return avg_score, a_cost, t_cost


async def evaluate_problem(annotation: dict, graph: Callable, log_path) -> Tuple[str, str, float]:
    expected_output = annotation["ref_text"]
    inputs = annotation["context"]
    answers = expected_output.split("|")

    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            output, cost = await graph(inputs) if graph else (None, None)

            f1_scores = []

            # if "|" in the output, split it and calculate the score for each part
            for answer in answers:
                if answer.strip() != "":
                    output_parts = output.split("|")
                    for output_part in output_parts:
                        f1_score, _ = calculate_score(answer, output_part)
                        f1_scores.append(f1_score)

            uni_score = max(f1_scores)

            print("uni_score", uni_score)

            if uni_score < 0.3:
                log_mismatch(inputs, expected_output, output, output, log_path)
            else:
                ensure_log_file_exists(log_path)

            break

        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = e
                uni_score = 0.0
                cost = None
                break

    return inputs, output, expected_output, uni_score, cost

async def evaluate_all_questions(data: List[Tuple[str, Dict[str, Any]]], graph: Callable, path, max_concurrent_tasks: int = 50) -> List[List[Any]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph, path)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating DROP problems", total=len(data))


async def optimize_drop_evaluation(graph: Callable, file_path: str, path: str, va_list: list):
    data = await load_data(file_path, va_list)
    results = await evaluate_all_questions(data, graph, path, max_concurrent_tasks=25)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on DROP dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost

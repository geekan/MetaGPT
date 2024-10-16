import json
import asyncio
import aiofiles
import pandas as pd
import numpy as np
from typing import List, Tuple, Callable, Set
from collections import Counter
from tqdm.asyncio import tqdm_asyncio
import string
import re
import os
from datetime import datetime

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

def calculate_score(ground_truth: str, prediction: str):
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

def log_mismatch(problem: str, expected_output: float, prediction: str, predicted_number, path):
    log_data = {
        "question": problem,
        "right_answer": expected_output,
        "model_output": prediction,
        "extracted_output": predicted_number
    }

    log_file = os.path.join(path, 'log.json')

    # 检查log文件是否已经存在
    if os.path.exists(log_file):
        # 如果存在，加载现有的日志数据
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        # 如果不存在，创建一个新的日志列表
        data = []

    # 添加新的日志记录
    data.append(log_data)

    # 将数据写回到log.json文件
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def load_data(file_path: str, specific_indices: List[int] = None) -> List[dict]:
    data = []
    # 异步读取文件内容
    async with aiofiles.open(file_path, mode="r", encoding='utf-8') as file:
        async for line in file:
            data.append(json.loads(line))

    # 然后在随机选择的样本中基于特定索引列表进行进一步筛选
    if specific_indices is not None:
        filtered_data = [data[i] for i in specific_indices if i < len(data)]
        return filtered_data

    return data

def save_results_to_csv(results: List[Tuple[str, str, str, str, float, float]], path):
    # 创建 DataFrame
    df = pd.DataFrame(results, columns=["question", "context", "prediction", "expected_output", "score", "cost"])

    # 计算统计数据
    avg_score = df["score"].mean()
    t_cost = df["cost"].max()
    a_cost = t_cost / len(df) if len(df) > 0 else 0

    # 获取当前时间，格式为 YYYYMMDD_HHMMSS
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成文件名，包含平均分和当前时间，保留五位小数
    filename = f"{avg_score:.5f}_{current_time}.csv"
    output_file = os.path.join(path, filename)

    # 保存到 CSV
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return avg_score, a_cost, t_cost

async def evaluate_problem(problem: dict, graph: Callable, log_path: str):
    input_text = problem["question"]
    expected_output = problem["answer"]
    paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
    context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)

    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            output, cost = await graph(input_text, context_str) if graph else "None"
            uni_score, extracted_output = calculate_score(expected_output, output)

            if uni_score == 0:
                log_mismatch(input_text, expected_output, output, extracted_output, log_path)
            else:
                ensure_log_file_exists(log_path)

            break
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = e
                cost = None
                uni_score = 0
                break

    return input_text, context_str, output, expected_output, uni_score, cost

async def evaluate_problem_optimize(problem: dict, graph: Callable, log_path: str):
    input_text = problem["question"]
    expected_output = problem["answer"]
    paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
    context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
    inputs = f"Context: {context_str}\n\nQuestion: {input_text}\n\nAnswer:"

    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            output, cost = await graph(inputs) if graph else "None"
            uni_score, extracted_output = calculate_score(expected_output, output)

            if uni_score == 0:
                log_mismatch(input_text, expected_output, output, extracted_output, log_path)
            else:
                ensure_log_file_exists(log_path)

            break
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = e
                cost = None
                uni_score = 0
                break

    return input_text, context_str, output, expected_output, uni_score, cost


async def evaluate_all_problems(data: List[dict], graph: Callable, path, max_concurrent_tasks: int = 50):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem_optimize(problem, graph, path)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating HotpotQA problems", total=len(data))

async def optimize_hotpotqa_evaluation(graph: Callable, file_path: str, path: str, va_list: list):
    data = await load_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=20)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on HotpotQA dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost

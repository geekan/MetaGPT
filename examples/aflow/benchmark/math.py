import re
import regex
from pandas import Series
from sympy import N, simplify
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr
from math import isclose
import multiprocessing
import json
import asyncio
import aiofiles
import pandas as pd
from typing import Optional, List, Tuple, Callable, Union, Any
from tqdm.asyncio import tqdm_asyncio
from datetime import datetime
import os
import inspect


def extract_model_answer(text: str) -> str:
    # 提取最后一个 \boxed{...}
    pattern = r"\\boxed{((?:[^{}]|{[^{}]*})*)}"
    boxed_matches = re.findall(pattern, text, re.DOTALL)
    if boxed_matches:
        return boxed_matches[-1].strip()

    # 提取最后一句话
    sentence_end_pattern = r'(?<!\d)[.!?]\s+'
    sentences = re.split(sentence_end_pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences[-1] if sentences else ""

def extract_answer(text: str) -> str:
    # Look for the answer within \boxed{...}
    boxed_match = re.search(r"\\boxed{(.*?)}", text)
    if boxed_match:
        return boxed_match.group(1).strip()

    sentence_end_pattern = r'(?<!\d)[.!?]\s+'
    sentences = re.split(sentence_end_pattern, text)

    # 过滤空字符串并返回最后一个非空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences[-1] if sentences else ""

def get_function_code(func):
    try:
        source_code = inspect.getsource(func)
        return source_code
    except OSError:
        return "no code"

def parse_digits(num):
    # format: 234.23 || 23%
    num = regex.sub(",", "", str(num))
    try:
        return float(num)
    except:
        if num.endswith("%"):
            num = num[:-1]
            if num.endswith("\\"):
                num = num[:-1]
            try:
                return float(num) / 100
            except:
                pass
    return None


def is_digit(num):
    # paired with parse_digits
    return parse_digits(num) is not None


def symbolic_equal(a, b):
    def _parse(s):
        for f in [parse_latex, parse_expr]:
            try:
                return f(s)
            except:
                pass
        return s

    a = _parse(a)
    b = _parse(b)

    try:
        if simplify(a - b) == 0:
            return True
    except:
        pass

    try:
        if isclose(N(a), N(b), abs_tol=1e-3):
            return True
    except:
        pass
    return False


def call_with_timeout(func, *args, timeout=5, **kwargs):
    output_queue = multiprocessing.Queue()
    process_args = args + (output_queue,)
    process = multiprocessing.Process(target=func, args=process_args, kwargs=kwargs)
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return False

    return output_queue.get()


def math_equal(
        prediction: Union[bool, float, str],
        reference: Union[float, str],
        include_percentage: bool = True,
        is_close: bool = True,
        timeout: bool = False,
) -> bool:
    """
    Exact match of math if and only if:
    1. numerical equal: both can convert to float and are equal
    2. symbolic equal: both can convert to sympy expression and are equal
    """
    if str(prediction) == str(reference):
        return True

    try:  # 1. numerical equal
        if is_digit(prediction) and is_digit(reference):
            prediction = parse_digits(prediction)
            reference = parse_digits(reference)
            # number questions
            if include_percentage:
                gt_result = [reference / 100, reference, reference * 100]
            else:
                gt_result = [reference]
            for item in gt_result:
                try:
                    if is_close:
                        if isclose(item, prediction, abs_tol=1e-3):
                            return True
                    else:
                        if item == prediction:
                            return True
                except Exception:
                    continue
            return False
    except:
        pass

    if not prediction and prediction not in [0, False]:
        return False

    # 2. symbolic equal
    reference = str(reference).strip()
    prediction = str(prediction).strip()

    if (
            regex.match(r"(\(|\[).+(\)|\])", prediction) is not None
            and regex.match(r"(\(|\[).+(\)|\])", reference) is not None
    ):
        pred_parts = prediction[1:-1].split(",")
        ref_parts = reference[1:-1].split(",")
        if len(pred_parts) == len(ref_parts):
            if all(
                    [
                        math_equal(pred_parts[i], ref_parts[i], include_percentage, is_close)
                        for i in range(len(pred_parts))
                    ]
            ):
                return True

    if (
            (prediction.startswith("\\begin{pmatrix}") or prediction.startswith("\\begin{bmatrix}"))
            and (prediction.endswith("\\end{pmatrix}") or prediction.endswith("\\end{bmatrix}"))
            and (reference.startswith("\\begin{pmatrix}") or reference.startswith("\\begin{bmatrix}"))
            and (reference.endswith("\\end{pmatrix}") or reference.endswith("\\end{bmatrix}"))
    ):
        pred_lines = [
            line.strip()
            for line in prediction[len("\\begin{pmatrix}"): -len("\\end{pmatrix}")].split("\\\\")
            if line.strip()
        ]
        ref_lines = [
            line.strip()
            for line in reference[len("\\begin{pmatrix}"): -len("\\end{pmatrix}")].split("\\\\")
            if line.strip()
        ]
        matched = True
        if len(pred_lines) == len(ref_lines):
            for pred_line, ref_line in zip(pred_lines, ref_lines):
                pred_parts = pred_line.split("&")
                ref_parts = ref_line.split("&")
                if len(pred_parts) == len(ref_parts):
                    if not all(
                            [
                                math_equal(pred_parts[i], ref_parts[i], include_percentage, is_close)
                                for i in range(len(pred_parts))
                            ]
                    ):
                        matched = False
                        break
                else:
                    matched = False
                if not matched:
                    break
        else:
            matched = False
        if matched:
            return True

    if prediction.count("=") == 1 and reference.count("=") == 1:
        pred = prediction.split("=")
        pred = f"{pred[0].strip()} - ({pred[1].strip()})"
        ref = reference.split("=")
        ref = f"{ref[0].strip()} - ({ref[1].strip()})"
        if symbolic_equal(pred, ref) or symbolic_equal(f"-({pred})", ref):
            return True
    elif prediction.count("=") == 1 and len(prediction.split("=")[0].strip()) <= 2 and "=" not in reference:
        if math_equal(prediction.split("=")[1], reference, include_percentage, is_close):
            return True
    elif reference.count("=") == 1 and len(reference.split("=")[0].strip()) <= 2 and "=" not in prediction:
        if math_equal(prediction, reference.split("=")[1], include_percentage, is_close):
            return True

    # symbolic equal with sympy
    if timeout:
        if call_with_timeout(symbolic_equal, prediction, reference):
            return True
    else:
        if symbolic_equal(prediction, reference):
            return True

    return False


def calculate_score(expected_output: str, prediction: str) -> tuple[int, str]:
    expected_answer = extract_model_answer(expected_output)
    predicted_answer = extract_model_answer(prediction)

    if math_equal(predicted_answer, expected_answer):
        return 1, predicted_answer
    else:
        return 0, predicted_answer


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

    # 获取传入函数的源代码
    function_code = get_function_code(extract_model_answer)
    log_data["extract_answer_code"] = function_code  # 新字段

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


def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
    # 创建 DataFrame
    df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])

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


async def evaluate_problem(problem: dict, graph, log_path) -> Tuple[str, str, str, int, str]:
    input_text = problem["problem"]
    expected_output = problem["solution"]
    max_retries = 2
    retries = 0



    prediction = await graph(input_text) if graph else "None"
    cost = prediction[1]
    output = prediction[0]

    uni_score, extracted_output = calculate_score(expected_output, output)

    if uni_score == 0:
        log_mismatch(input_text, expected_output, output, extracted_output, log_path)
    else:
        ensure_log_file_exists(log_path)

    # while retries < max_retries:
    #     try:
    #         prediction = await graph(input_text) if graph else "None"
    #         cost = prediction[1]
    #         output = prediction[0]

    #         uni_score, extracted_output = calculate_score(expected_output, output)

    #         if uni_score == 0:
    #             log_mismatch(input_text, expected_output, output, extracted_output, log_path)
    #         else:
    #             ensure_log_file_exists(log_path)

    #         break

    #     except Exception as e:
    #         retries += 1
    #         print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

    #         if retries == max_retries:
    #             print("Maximum retries reached. Skipping this sample.")
    #             output = e
    #             cost = None
    #             uni_score = 0
    #             break

    return input_text, output, expected_output, uni_score, cost


async def evaluate_all_problems(data: List[dict], graph, path, max_concurrent_tasks: int = 300):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph, path)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating MATH problems", total=len(data))


async def optimize_math_evaluation(graph: Callable, file_path: str, path: str, va_list: list) -> tuple[
    Any, Any, Any]:
    data = await load_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=30)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on MATH dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost

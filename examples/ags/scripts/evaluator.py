# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : evaluate for different dataset

import asyncio
import json
import multiprocessing
import re
from math import isclose
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

import aiofiles
import numpy as np
import pandas as pd
import regex
from scipy.optimize import linear_sum_assignment
from sympy import N, simplify
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr
from tqdm.asyncio import tqdm_asyncio

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQA", "DROP"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path

    def _generate_random_indices(self, n, n_samples, test=False):
        """
        生成随机索引
        """

        def _set_seed(seed=42):
            np.random.seed(seed)

        _set_seed()
        indices = np.arange(n)
        np.random.shuffle(indices)
        if test:
            return indices[n_samples:]
        else:
            return indices[:n_samples]

    def validation_evaluate(self, dataset: DatasetType, graph, params: dict, path):
        """
        Evaluates on validation dataset.
        """
        if dataset == "Gsm8K":
            return self._gsm8k_eval(graph, params, path)
        elif dataset == "MATH":
            self._math_eval(graph, params, path)
        elif dataset == "HumanEval":
            return self._humaneval_eval(graph, params)
        elif dataset == "HotpotQA":
            return self._hotpotqa_eval(graph, params)
        elif dataset == "MBPP":
            return self._mbpp_eval(graph, params)
        elif dataset == "DROP":
            return self._drop_eval(graph, params)

    def test_evaluate(self, dataset: DatasetType):
        """
        Evaluates on test dataset.
        """
        pass

    async def _gsm8k_eval(self, graph_class, params, path, samples: int = 50):
        """
        Evaluate on GSM8K dataset.
        """

        # 模拟加载模型的函数
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="Gsm8K", llm_config=llm_config, dataset=dataset)
            return graph

        # 清理文本并提取单个数字
        def extract_number(text: str) -> Optional[float]:
            # 使用正则表达式提取数字，包括整数和浮点数
            matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", text)
            print(matches)
            if matches:
                # 获取最后一个匹配的数字
                last_number = matches[-1]

                # 移除逗号以统一格式
                last_number = last_number.replace(",", "")

                try:
                    return float(last_number)
                except ValueError:
                    return None
            else:
                return None

        # 宽松匹配分数计算函数
        def loose_match_score(expected_output: str, prediction: str, tolerance: float = 1e-6) -> int:
            expected_number = extract_number(expected_output)
            predicted_number = extract_number(prediction)

            print(predicted_number)

            # 如果预期输出或预测输出为空，返回不匹配
            if expected_number is None or predicted_number is None:
                return 0

            # 比较两个提取出的数字，允许一定的容差
            if abs(expected_number - predicted_number) <= tolerance:
                return 1  # 数字相近，认为匹配成功
            else:
                return 0  # 数字不匹配

        # 异步评估单个问题
        async def _evaluate_problem(input: str, graph, expected_output: str) -> Tuple[str, str, str, int, str]:
            prompt = input
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    # 假设模型有一个异步生成函数
                    prediction = await graph(prompt) if graph else "None"  # 这是一个占位符，替换成实际的模型生成逻辑
                    cost = prediction[1]
                    output = prediction[0]["solution"]

                    score = loose_match_score(expected_output, prediction[0]["solution"])
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        output = None
                        cost = None
                        score = 0
                        break

            return input, output, expected_output, score, cost

        # 异步读取JSONL文件
        async def load_data(file_path: str) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            return data[:samples]

        # 并行评估所有问题
        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 300):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    input_text = problem["question"]
                    expected_output = problem["answer"]
                    return await _evaluate_problem(input_text, graph, expected_output)

            tasks = [sem_evaluate(problem) for problem in data]

            # 使用tqdm.gather来显示进度条
            return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

        # 保存结果到CSV文件
        def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
            df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])
            average_score = df["score"].mean()

            # 生成文件名，保留五位小数
            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def gsm8k():
            file_path = "examples/ags/w_action_node/data/gsm8k.jsonl"  # 替换为您的JSONL文件路径
            data = await load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            # 保存结果到CSV文件并获取平均分
            average_score = save_results_to_csv(results, path=path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await gsm8k()

        return score

    async def _math_eval(self, graph_class, params, path, samples: int = 200):
        """
        Evaluate on MATH dataset.
        """

        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="MATH", llm_config=llm_config, dataset=dataset)
            return graph

        def extract_answer(text: str) -> str:
            # Look for the answer within \boxed{...}
            boxed_match = re.search(r"\\boxed{(.*?)}", text)
            if boxed_match:
                return boxed_match.group(1)

            # If no \boxed{...}, return the last sentence
            sentences = text.split(".")
            return sentences[-1].strip() if sentences else ""

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
                    for line in prediction[len("\\begin{pmatrix}") : -len("\\end{pmatrix}")].split("\\\\")
                    if line.strip()
                ]
                ref_lines = [
                    line.strip()
                    for line in reference[len("\\begin{pmatrix}") : -len("\\end{pmatrix}")].split("\\\\")
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

        def calculate_score(expected_output: str, prediction: str) -> int:
            expected_answer = extract_answer(expected_output)
            predicted_answer = extract_answer(prediction)

            return 1 if math_equal(predicted_answer, expected_answer) else 0

        async def _evaluate_problem(problem: dict, graph) -> Tuple[str, str, str, int, str]:
            input_text = problem["problem"]
            expected_output = problem["solution"]
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    prediction = await graph(input_text) if graph else "None"
                    cost = prediction[1]
                    output = prediction[0]["solution"]

                    score = calculate_score(expected_output, output)
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        output = None
                        cost = None
                        score = 0
                        break

            return input_text, output, expected_output, score, cost

        async def load_data(file_path: str) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            return data[:samples]

        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 300):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    return await _evaluate_problem(problem, graph)

            tasks = [sem_evaluate(problem) for problem in data]

            return await tqdm_asyncio.gather(*tasks, desc="Evaluating MATH problems", total=len(data))

        def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
            df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])
            average_score = df["score"].mean()

            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def math_evaluation():
            file_path = "examples/ags/w_action_node/data/math.jsonl"  # Replace with the actual path to MATH.jsonl
            data = await load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            average_score = save_results_to_csv(results, path=path)

            print(f"Average score on MATH dataset: {average_score:.5f}")
            return average_score

        score = await math_evaluation()

        return score

    async def _humaneval_eval(self, graph_class, params, test=False):
        """
        Evaluate on HumanEval dataset.
        """
        PASS = "pass"
        FAIL = "fail"

        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="HumanEval", llm_config=llm_config, dataset=dataset)
            return graph

        async def load_data(file_path: str, samples=1) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            random_indices = self._generate_random_indices(len(data), samples)
            data = [data[i] for i in random_indices]
            return data

        async def check_solution(solution, test_cases, entry_point):
            # Define a local dictionary to execute the solution
            local_dict = {}
            exec("from typing import List\n\n" + solution, {}, local_dict)

            # Ensure the entry point function is defined
            if entry_point not in local_dict:
                raise ValueError(f"Function {entry_point} is not defined in the solution.")

            details = [False for _ in range(len(test_cases))]

            # Check each test case
            for i, test in enumerate(test_cases):
                # Replace 'candidate' with the actual function call
                test_expr = test.replace("candidate", entry_point)
                try:
                    # Evaluate the test case
                    if eval(test_expr, {}, local_dict):
                        details[i] = True
                except Exception as e:
                    print(f"Error evaluating test case '{test}': {e}")

            if all(details):
                return PASS, details

            return FAIL, details

        async def _evaluate_problem(data, graph) -> Tuple[str, str, str, int]:
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    solution = await graph(data["prompt"]) if graph else "None"
                    ret = await check_solution(solution, data["test_cases"], data["entry_point"])

                    score = 1 if ret[0] == PASS else 0
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        solution = None
                        ret = (FAIL, [])
                        score = 0
                        break

            return data["prompt"], solution, ret[1], score

        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 50):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    return await _evaluate_problem(problem, graph)

            tasks = [sem_evaluate(problem) for problem in data]

            return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

        def save_results_to_jsonl(results: List[Tuple[str, str, str, int]], path):
            avg_score = 0

            with open(path, "w") as f:
                for result in results:
                    f.write(
                        json.dumps(
                            {
                                "question": result[0],
                                "prediction": result[1],
                                "test_case_details": result[2],
                                "score": result[3],
                            }
                        )
                        + "\n"
                    )
                    avg_score += result[3]
            print(f"Results saved to {path}")
            avg_score /= len(results)

            return avg_score

        async def humaneval():
            file_path = "examples/ags/scripts/data/human-eval-new.jsonl"
            data = await load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            # 保存结果到JSONL文件并获取平均分
            average_score = save_results_to_jsonl(results, path=self.eval_path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await humaneval()

        return score

    async def _hotpotqa_eval(self, graph_class, params, test=False):
        """
        Evaluate on HotpotQA dataset.
        """

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

        # def exact_match_score(prediction, ground_truth):
        #     return int(normalize_answer(prediction) == normalize_answer(ground_truth))

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

        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="HotpotQA", llm_config=llm_config, dataset=dataset)
            return graph

        async def load_data(file_path: str, samples=20) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            random_indices = self._generate_random_indices(len(data), samples)
            data = [data[i] for i in random_indices]
            return data

        async def _evaluate_problem(input: str, context_str: str, graph, expected_output: str):
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    # TODO Hotpotqa Graph 需要修改输入和输出
                    prediction, supporting_sentences = await graph(input, context_str) if graph else "None"
                    predicted_bags = answer_to_bags(prediction)
                    gold_bags = answer_to_bags(expected_output)

                    if set(predicted_bags[0]) == set(gold_bags[0]):
                        pass
                    else:
                        pass

                    f1_per_bag = _align_bags(predicted_bags[1], gold_bags[1])
                    score = np.mean(f1_per_bag)
                    # f1 = round(f1, 2)

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

        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 50):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    input_text = problem["question"]
                    expected_output = problem["answer"]
                    paragraphs = [item[1] for item in problem["context"] if isinstance(item[1], list)]
                    context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
                    return await _evaluate_problem(input_text, context_str, graph, expected_output)

            tasks = [sem_evaluate(problem) for problem in data]

            return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

        # def save_results_to_jsonl(results: List[Tuple[str, str, str, str, int]], path):
        #     avg_score = 0

        #     with open(path, "w") as f:
        #         for result in results:
        #             f.write(json.dumps({"question": result[0], "prediction": result[1], "expected_output": result[2], "supporting_sentences": result[3], "score": result[4]}) + "\n")
        #             avg_score += result[4]
        #     print(f"Results saved to {path}")
        #     avg_score /= len(results)

        #     return avg_score

        def save_results_to_csv(results: List[Tuple[str, str, str, str, int]], path):
            df = pd.DataFrame(
                results, columns=["question", "prediction", "expected_output", "supporting_sentences", "score"]
            )
            average_score = df["score"].mean()

            # 生成文件名，保留五位小数
            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def hotpotqa():
            file_path = "examples/ags/scripts/data/hotpotqa.jsonl"  # 替换为您的JSONL文件路径
            data = await load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            # 保存结果到JSONL文件并获取平均分
            average_score = save_results_to_csv(results, path=self.eval_path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await hotpotqa()

        return score

    async def _mbpp_eval(self, graph_class, params, test=False):
        """
        Evaluate on MBPP dataset.
        """

        PASS = "pass"
        FAIL = "fail"

        async def load_data(file_path: str, samples=1) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            random_indices = self._generate_random_indices(len(data), samples)
            data = [data[i] for i in random_indices]
            return data

        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="MBPP", llm_config=llm_config, dataset=dataset)
            return graph

        async def check_solution(solution, test_cases, timeout=1):
            # Define a local dictionary to execute the solution
            local_dict = {}
            exec(solution, {}, local_dict)

            details = [False for _ in range(len(test_cases))]

            async def evaluate_test(test):
                # Delete 'assert' from test
                test_expr = test.replace("assert ", "")
                try:
                    # Evaluate the test case with timeout
                    await asyncio.wait_for(asyncio.to_thread(eval, test_expr, {}, local_dict), timeout)
                    return True
                except asyncio.TimeoutError:
                    print(f"Test case '{test}' timed out.")
                except Exception as e:
                    print(f"Error evaluating test case '{test}': {e}")
                return False

            # Check each test case
            for i, test in enumerate(test_cases):
                result = await evaluate_test(test)
                details[i] = result
                if not result:
                    return FAIL, details

            if all(details):
                return PASS, details

            return FAIL, details

        async def _evaluate_problem(data, graph) -> Tuple[str, str, str, int]:
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    solution = await graph(data["prompt"]) if graph else "None"
                    ret = await check_solution(solution, data["test_list"])

                    score = 1 if ret[0] == PASS else 0
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        solution = None
                        ret = (FAIL, [])
                        score = 0
                        break

            return data["prompt"], solution, ret[1], score

        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 50):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    return await _evaluate_problem(problem, graph)

            tasks = [sem_evaluate(problem) for problem in data]

            return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

        def save_results_to_csv(results: List[Tuple[str, str, str, str, int]], path):
            df = pd.DataFrame(results, columns=["question", "prediction", "test_case_details", "score"])
            average_score = df["score"].mean()

            # 生成文件名，保留五位小数
            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def mbpp():
            file_path = "examples/ags/scripts/data/mbpp-new.jsonl"
            data = await load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            # 保存结果到JSONL文件并获取平均分
            average_score = save_results_to_csv(results, path=self.eval_path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await mbpp()

        return score

    async def _drop_eval(self, graph_class, params, test=False):
        """
        Evaluate on DROP dataset.
        """

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

        # def exact_match_score(prediction, ground_truth):
        #     return int(normalize_answer(prediction) == normalize_answer(ground_truth))

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

        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]

            graph = graph_class(name="HotpotQA", llm_config=llm_config, dataset=dataset)
            return graph

        def load_data(file_path: str, samples=1) -> List[dict]:
            with open(file_path, mode="r") as file:
                data = json.load(file)
                data = list(data.items())
            random_indices = self._generate_random_indices(len(data), samples)
            data = [data[i] for i in random_indices]
            return data

        async def _evaluate_problem(question, passage, answers, graph):
            max_retries = 5
            retries = 0

            def answer_json_to_strings(answer: Dict[str, Any]) -> Tuple[Tuple[str, ...], str]:
                """
                Takes an answer JSON blob from the DROP data release and converts it into strings used for
                evaluation.
                """
                if "number" in answer and answer["number"]:
                    return tuple([str(answer["number"])]), "number"
                elif "spans" in answer and answer["spans"]:
                    return tuple(answer["spans"]), "span" if len(answer["spans"]) == 1 else "spans"
                elif "date" in answer:
                    return (
                        tuple(
                            [
                                "{0} {1} {2}".format(
                                    answer["date"]["day"], answer["date"]["month"], answer["date"]["year"]
                                )
                            ]
                        ),
                        "date",
                    )
                else:
                    raise ValueError(
                        f"Answer type not found, should be one of number, spans or date at: {json.dumps(answer)}"
                    )

            prediction = await graph(question, passage) if graph else "None"
            while retries < max_retries:
                try:

                    def get_f1_score(prediction: str, golden_answer: str) -> float:
                        predicted_bags = answer_to_bags(prediction)
                        gold_bags = answer_to_bags(golden_answer)

                        if set(predicted_bags[0]) == set(gold_bags[0]):
                            pass
                        else:
                            pass

                        f1_per_bag = _align_bags(predicted_bags[1], gold_bags[1])
                        score = np.mean(f1_per_bag)
                        return score

                    max_score = 0.0
                    best_answer = None
                    for answer in answers:
                        golden_answer, _ = answer_json_to_strings(answer)
                        golden_answer = golden_answer[0]
                        score = get_f1_score(prediction, golden_answer)
                        if score > max_score:
                            max_score = score
                            best_answer = golden_answer

                    break
                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")

                        max_score = 0
                        break

            return best_answer, prediction, max_score

        async def evaluate_all_passages(annotations, graph, max_concurrent_tasks: int = 50):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)
            results = []

            async def sem_evaluate(id, annotation):
                async with semaphore:
                    passage = annotation["passage"]
                    for qa_pair in annotation["qa_pairs"]:
                        question = qa_pair["question"]
                        answers = [qa_pair["answer"]]
                        if "validated_answers" in qa_pair and qa_pair["validated_answers"]:
                            answers.extend(qa_pair["validated_answers"])
                        best_answer, prediction, score = await _evaluate_problem(question, passage, answers, graph)
                        results.append([id, question, prediction, best_answer, score])

            tasks = [sem_evaluate(id, annotation) for id, annotation in annotations]
            await tqdm_asyncio.gather(*tasks, desc="Evaluating passages", total=len(annotations))

            return results

        def save_results_to_csv(results: List[Tuple[str, str, str, str, int]], path):
            df = pd.DataFrame(results, columns=["id", "question", "prediction", "best_answer", "score"])
            average_score = df["score"].mean()

            # 生成文件名，保留五位小数
            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def drop():
            file_path = "examples/ags/scripts/data/drop_dataset_dev.json"  # 替换为您的JSONL文件路径
            data = load_data(file_path)

            graph = await load_graph()

            results = await evaluate_all_passages(data, graph, max_concurrent_tasks=20)

            # 保存结果到JSONL文件并获取平均分
            average_score = save_results_to_csv(results, path=self.eval_path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await drop()

        return score

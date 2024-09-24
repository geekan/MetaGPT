# -*- coding: utf-8 -*-
# @Date    : 8/12/2024 22:00 PM
# @Author  : issac
# @Desc    : optimizer for graph

import ast
import asyncio
import json
import os
import re
import time
from collections import defaultdict
from typing import List, Literal
import datetime
import random
import pandas as pd
import traceback

import numpy as np
from pydantic import BaseModel, Field

from examples.ags.scripts.evaluator import Evaluator
from examples.ags.scripts.prompts.optimize_prompt import (
    GRAPH_CUSTOM_USE,
    GRAPH_INPUT,
    GRAPH_OPTIMIZE_PROMPT,
    GRAPH_TEMPLATE
)
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import create_llm_instance

config_iterate_path = "iterate"

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]
QuestionType = Literal["math", "code", "quiz"]
OptimizerType = Literal["Graph", "Test"]


class OperatorExtend(BaseModel):
    name: str = Field(default="", description="name")
    description: str = Field(default="", description="description")
    prompt: str = Field(default="", description="prompt")

class OperatorSelect(BaseModel):
    selected_operators: str = Field(default="", description="selected operators")


class OperatorOptimze(BaseModel):
    modification: str = Field(default="", description="modification")
    prompt: str = Field(default="", description="prompt")
    operator: str = Field(default="", description="operator")


class GraphOptimize(BaseModel):
    modification: str = Field(default="", description="modification")
    graph: str = Field(default="", description="graph")
    prompt: str = Field(default="", description="prompt")


class Optimizer:
    def __init__(
        self,
        dataset: DatasetType,
        opt_llm_config,
        exec_llm_config,
        operators: List,
        sample: int ,
        optimized_path: str = None,
        question_type: QuestionType = "math",  # math,code,quiz
    ) -> None:
        self.optimize_llm_config = opt_llm_config
        self.optimize_llm = create_llm_instance(self.optimize_llm_config)
        self.execute_llm_config = exec_llm_config

        self.dataset = dataset
        self.type = question_type

        self.graph = None  # 当前的执行图，在optimize过程中加载
        self.operators = operators

        self.root_path = f"{optimized_path}/{self.dataset}"
        self.sample = sample # 从过去的轮次中采样的数量
        self.top_scores = []
        self.round = 1  # 起始轮次

    def optimize(self, mode: OptimizerType = "Graph", max_rounds: int = 30):
        """
        Generate and optimize the workflow for given dataset.
        """
        if mode == "Test":
            for i in range(3):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                score = loop.run_until_complete(self.test())

            return None

        for opt_round in range(max_rounds):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            retry_count = 0
            max_retries = 5

            # retry in optimize workflow's processs
            while retry_count < max_retries:
                try:
                    score = loop.run_until_complete(self._optimize_graph())
                    break  
                except Exception as e:
                    retry_count += 1
                    print(f"Error occurred: {e}. Retrying... (Attempt {retry_count}/{max_retries})")
                    if retry_count == max_retries:
                        print("Max retries reached. Moving to next round.")
                        score = None  # 或者设置一个默认分数

                    wait_time = 5 * retry_count
                    time.sleep(wait_time)  # 在重试之前等待一段时间


                if retry_count < max_retries:
                    # 如果还需要重试，创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            self.round += 1
            print(f"Score for round {self.round}: {score}")
            time.sleep(5)

    def _load_graph(self, round_number, graphs_path):
        """
        动态加载指定轮次的 Graph 类。
        """
        graphs_path = graphs_path.replace("\\", ".").replace("/", ".")
        graph_module_name = f"{graphs_path}.round_{round_number}.graph"

        try:
            graph_module = __import__(graph_module_name, fromlist=[""])
            graph_class = getattr(graph_module, "SolveGraph")
            self.graph = graph_class
        except ImportError as e:
            print(f"Error loading graph for round {round_number}: {e}")
            raise

    def _read_graph_files(self, round_number, graphs_path):
        """
        动态读取指定轮次的 Prompt和Graph。
        """
        # 构建 prompt.py 文件的相对路径
        # examples/ags/scripts/optimized/Gsm8k/graphs/round_1
        prompt_file_path = os.path.join(graphs_path, f"round_{round_number}", "prompt.py")
        graph_file_path = os.path.join(graphs_path, f"round_{round_number}", "graph.py")

        try:
            with open(prompt_file_path, "r", encoding="utf-8") as file:
                prompt_content = file.read()
            with open(graph_file_path, "r", encoding="utf-8") as file:
                graph_content = file.read()

        except FileNotFoundError as e:
            print(f"Error: File not found for round {round_number}: {e}")
            raise
        except Exception as e:
            print(f"Error loading prompt for round {round_number}: {e}")
            raise
        return prompt_content, graph_content

    def _load_scores(self, path=None, mode="Graph"):
        if mode == "Graph":
            rounds_dir = os.path.join(self.root_path, "graphs")
        else:
            rounds_dir = path

        result_file = os.path.join(rounds_dir, "results.json")
        self.top_scores = []

        with open(result_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        df = pd.DataFrame(data)

        # 直接计算每一轮的平均分数
        scores_per_round = df.groupby('round')['score'].mean().to_dict()

        # 存储每一轮的平均分数
        for round_number, average_score in scores_per_round.items():
            self.top_scores.append({
                "round": round_number,
                "score": average_score
            })

        # 对所有轮次的分数进行排序
        self.top_scores.sort(key=lambda x: x["score"], reverse=True)

        return self.top_scores

    def _compute_probabilities(self, scores, alpha=0.2, lambda_=0.3):
        """
        计算混合概率分布，结合基础概率和分数加权概率。

        Args:
            scores (list or np.ndarray): 分数列表或数组。
            alpha (float): 控制分数权重敏感度的参数。
            lambda_ (float): 控制基础概率与分数加权概率的混合比例。取值范围 [0, 1]。

        Returns:
            np.ndarray: 归一化后的混合概率分布。
        """
        scores = np.array(scores, dtype=np.float64)
        n = len(scores)

        if n == 0:
            raise ValueError("分数列表为空。")

        # 基础概率（均匀分布）
        uniform_prob = np.full(n, 1.0 / n, dtype=np.float64)

        # 分数加权概率
        max_score = np.max(scores)
        shifted_scores = scores - max_score
        exp_weights = np.exp(alpha * shifted_scores)

        sum_exp_weights = np.sum(exp_weights)
        if sum_exp_weights == 0:
            raise ValueError("所有指数权重的和为0，无法归一化。")

        score_prob = exp_weights / sum_exp_weights

        # 混合概率分布
        mixed_prob = lambda_ * uniform_prob + (1 - lambda_) * score_prob

        # 归一化混合概率
        total_prob = np.sum(mixed_prob)
        if not np.isclose(total_prob, 1.0):
            mixed_prob = mixed_prob / total_prob

        return mixed_prob

    def _select_round(self, items):
        """
        从项列表中基于混合概率分布选择一个项。

        Args:
            items (list of dict): 包含'round'和'score'键的项列表。
            alpha (float): 控制分数权重敏感度的参数。
            lambda_ (float): 控制基础概率与分数加权概率的混合比例。取值范围 [0, 1]。

        Returns:
            dict: 被选中的项。
        """
        if not items:
            raise ValueError("项列表为空。")

        # 根据'score'字段对项进行降序排序
        sorted_items = sorted(items, key=lambda x: x["score"], reverse=True)

        # 提取分数列表
        scores = [item["score"] * 100 for item in sorted_items]


        # 计算混合概率分布
        probabilities = self._compute_probabilities(scores)
        print("\n混合概率分布: ", probabilities)

        # 基于概率分布选择一个索引
        selected_index = np.random.choice(len(sorted_items), p=probabilities)
        print(f"\n选择的索引: {selected_index}，选择的项: {sorted_items[selected_index]}")

        # 返回被选中的项
        return sorted_items[selected_index]

    def _get_top_rounds(self, path=None, mode="Graph"):
        """
        返回分数最高的 top_x 个轮次，并确保返回的轮次不重复。
        """
        self._load_scores(path, mode)
        # 创建一个集合来跟踪已包含的轮次
        unique_rounds = set()
        unique_top_scores = []

        # 首先，添加第一轮（轮次 1），如果它存在的话
        first_round = next((item for item in self.top_scores if item["round"] == 1), None)
        if first_round:
            unique_top_scores.append(first_round)
            unique_rounds.add(1)

        # 遍历 top_scores 列表
        for item in self.top_scores:
            if item["round"] not in unique_rounds:
                unique_top_scores.append(item)
                unique_rounds.add(item["round"])

                # 如果已经收集到了足够的唯一轮次，则提前终止循环
                if len(unique_top_scores) >= self.sample:
                    break

        return unique_top_scores

    def _load_experience(self, path=None, mode: str = "Graph"):
        if mode == "Graph":
            rounds_dir = os.path.join(self.root_path, "graphs")
        else:
            rounds_dir = path  # 这个path对应的是具体的operator的路径
        experience_data = defaultdict(lambda: {"score": None, "success": {}, "failure": {}})

        # 遍历所有轮次的文件夹
        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith("round_"):
                round_path = os.path.join(rounds_dir, round_dir)
                try:
                    # 提取轮次的数字
                    round_number = int(round_dir.split("_")[1])

                    # 查找 experience.json 文件
                    json_file_path = os.path.join(round_path, "experience.json")
                    if os.path.exists(json_file_path):
                        with open(json_file_path, "r", encoding="utf-8") as json_file:  # 指定 UTF-8 编码
                            data = json.load(json_file)
                            father_node = data["father node"]

                            # 如果这是该父节点的第一条记录，设置其分数
                            if experience_data[father_node]["score"] is None:
                                experience_data[father_node]["score"] = data["before"]

                            # 根据成功与否，将数据添加到相应的字典中
                            if data["succeed"]:
                                experience_data[father_node]["success"][round_number] = {
                                    "modification": data["modification"],
                                    "score": data["after"]
                                }
                            else:
                                experience_data[father_node]["failure"][round_number] = {
                                    "modification": data["modification"],
                                    "score": data["after"]
                                }
                    else:
                        print(f"experience.json not found for round {round_dir}")
                except Exception as e:
                    print(f"Error processing {round_dir}: {str(e)}")

        # 将 defaultdict 转换为普通 dict
        experience_data = dict(experience_data)

        # 保存为JSON文件
        # TODO 这里需要再check一下有没有冲突
        output_path = os.path.join(rounds_dir, "processed_experience.json")
        # output_path = os.path.join(self.root_path, "graphs", "processed_experience.json")

        with open(output_path, "w", encoding="utf-8") as outfile:  # 指定 UTF-8 编码
            json.dump(experience_data, outfile, indent=4, ensure_ascii=False)  # ensure_ascii=False 以正确保存中文字符

        print(f"Processed experience data saved to {output_path}")
        return experience_data

    def _load_log(self, cur_round, path=None, mode: str = "Graph"):
        if mode == "Graph":
            log_dir = os.path.join(self.root_path, "graphs", f"round_{cur_round}", "log.json")
        else:
            log_dir = path  # 这个path对应的是具体的operator的路径

        # 读取 JSON 文件
        with open(log_dir, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 确保数据是一个列表
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            # 如果数据既不是列表也不是字典，尝试将其转换为列表
            data = list(data)

        # 检查数据是否为空
        if not data:
            return ""  # 返回空字符串表示没有可用的日志

        # 随机选择最多三个元素
        sample_size = min(3, len(data))
        random_samples = random.sample(data, sample_size)

        # 组装为一个文本
        log = ""
        for sample in random_samples:
            log += json.dumps(sample, indent=4, ensure_ascii=False) + "\n\n"

        # 最终结果存储在 assembled_text 中
        return log

    def _load_operator_description(self, id, operator_name, file_path):
        """
        针对初始Operator，我们从最外层中读取
        对于修改后的Operator，我们从对应的round中读取
        """
        with open(file_path, "r") as f:
            operator_data = json.load(f)
            matched_data = operator_data[operator_name]
            desc = matched_data["description"]
            interface = matched_data["interface"]
            operator_description = f"{id}. {operator_name}: {desc}, with interface {interface})."
            return operator_description

    def _load_operators_description(self, mode: OptimizerType = "Graph", operators=None):
        if mode == "Graph":
            path = f"{self.root_path}/graphs/template/operator.json"
            operators = self.operators
        else:
            path = f"{self.root_path}/operators/template/operator.json"
        operators_description = ""
        for id, operator in enumerate(operators):
            operator_description = self._load_operator_description(id + 1, operator, path)
            operators_description += f"{operator_description}\n"

        return operators_description

    def _load_prompts_description(self, mode: OptimizerType = "Graph"):
        if mode == "Graph":
            path = f"{self.root_path}/graphs/template/prompt_lib.json"
        else:
            path = f"{self.root_path}/operators/template/prompt_lib.json"
        prompt_description = ""

        with open(path, "r") as f:
            operator_data = json.load(f)
            for key in operator_data.keys():
                data = operator_data[key]
                desc = data["description"]
                prompt_description += f"{key} description: {desc}\n"

        return prompt_description

    async def _optimize_graph(self):
        """
        Optimize Graph's Structure and Prompt
        """
        validation_n = 5
        try:
            # 获取项目的根目录
            graph_path = f"{self.root_path}/graphs"
            # 定义 JSON 文件路径
            result_path = os.path.join(graph_path, "results.json")

            # 如果文件存在，先读取已有的数据
            if os.path.exists(result_path):
                with open(result_path, 'r') as json_file:
                    try:
                        data = json.load(json_file)
                    except json.JSONDecodeError:
                        data = []  # 如果文件存在但格式错误，则重置为空列表
            else:
                data = []

            if self.round == 1:
                # 创建文件夹（如果不存在）
                directory = os.path.join(graph_path, f"round_{self.round}")
                os.makedirs(directory, exist_ok=True)

                self._load_graph(self.round, graph_path)

                evaluator = Evaluator(eval_path=directory)

                for i in range(validation_n):

                    score, avg_cost, total_cost = await evaluator.graph_evaluate(
                        self.dataset, self.graph, {"dataset": self.dataset, "llm_config": self.execute_llm_config},
                        directory, is_test=False
                    )

                    now = datetime.datetime.now()

                    # 新增的数据
                    new_data = {"round": self.round, "score": score, "avg_cost": avg_cost, "total_cost": total_cost, "time": now}

                    # 添加新数据到已有的数据列表中
                    data.append(new_data)

                    # 将更新后的数据写入 JSON 文件
                    with open(result_path, 'w') as json_file:
                        json.dump(data, json_file, default=str, indent=4)

            else:
                pass


            # 创建文件夹（如果不存在）
            directory = os.path.join(graph_path, f"round_{self.round + 1}")
            os.makedirs(directory, exist_ok=True)

            top_rounds = self._get_top_rounds()

            sample = self._select_round(top_rounds)

            print(sample)

            prompt, graph_load = self._read_graph_files(sample["round"], graph_path)
            score = sample["score"]

            # 正则表达式匹配 SolveGraph 开始的内容
            pattern = r"class SolveGraph:.+"

            # 使用re.findall找到所有匹配项
            graph = re.findall(pattern, graph_load, re.DOTALL)

            # 加载处理过的 experience 数据
            processed_experience = self._load_experience()

            # 获取当前轮次的 experience 数据
            current_round = int(sample["round"])  # 确保是字符串类型
            experience_data = processed_experience.get(current_round)
            log_data = self._load_log(current_round)

            if experience_data:
                # 构建 experience 字符串
                experience = f"Original Score: {experience_data['score']}\n"
                experience += "Here are some incorrect paths that should not be attempted again:\n```\n"
                for key, value in experience_data["failure"].items():
                    experience += f"- {value['modification']} (Score: {value['score']})\n"
                for key, value in experience_data["success"].items():
                    experience += f"- {value['modification']} \n"
                experience += "\n```\n\nNote: Take into account past failures and avoid repeating the same mistakes, as these failures indicate that these approaches are ineffective. You must fundamentally change your way of thinking, rather than simply using more advanced Python syntax like for, if, else, etc., or modifying the prompt."
            else:
                experience = f"No experience data found for round {current_round}."

            operator_description = self._load_operators_description()

            graph_input = GRAPH_INPUT.format(
                experience=experience, score=score, graph=graph[0], prompt=prompt, operator_description=operator_description, type=self.type, log=log_data
            )

            graph_system = GRAPH_OPTIMIZE_PROMPT.format(type=self.type)

            graph_optimize_prompt = graph_input+GRAPH_CUSTOM_USE+graph_system

            print(graph_optimize_prompt)

            # TODO 从这里开始，Graph Optimize 可以作为一个Operator放入 Operator.py 之中
            graph_optimize_node = await ActionNode.from_pydantic(GraphOptimize).fill(
                context=graph_optimize_prompt, mode="context_fill", llm=self.optimize_llm
            )

            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    response = graph_optimize_node.instruct_content.model_dump()
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction during graph optimize: {e}. Retrying... ({retries}/{max_retries})")
                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        break
                    traceback.print_exc()  # 打印堆栈信息以查看报错的具体位置
                    time.sleep(5)

            graph_match = response["graph"]
            prompt = response["prompt"]
            modification = response["modification"]

            graph = GRAPH_TEMPLATE.format(graph=graph_match, round=self.round + 1, dataset=self.dataset)

            # 将 graph.py 文件写入到目录中
            with open(os.path.join(directory, "graph.py"), "w", encoding="utf-8") as file:
                file.write(graph)

            # 将 prompt.py 文件写入到目录中
            with open(os.path.join(directory, "prompt.py"), "w", encoding="utf-8") as file:
                file.write(prompt)

            # 将 prompt.py 文件写入到目录中
            with open(os.path.join(directory, "__init__.py"), "w", encoding="utf-8") as file:
                file.write("")

            experience = {
                "father node": sample["round"],
                "modification": modification,
                "before": sample["score"],
                "after": None,
                "succeed": None,
            }

            self._load_graph(self.round + 1, graph_path)

            evaluator = Evaluator(eval_path=directory)

            print(self.graph)

            sum_score = 0

            for i in range(validation_n):

                score, avg_cost, total_cost = await evaluator.validation_evaluate(
                    self.dataset, self.graph, {"dataset": self.dataset, "llm_config": self.execute_llm_config},
                    directory
                )

                now = datetime.datetime.now()

                # 新增的数据
                new_data = {"round": self.round+1, "score": score, "avg_cost": avg_cost, "total_cost": total_cost, "time": now}

                # 添加新数据到已有的数据列表中
                data.append(new_data)

                # 将更新后的数据写入 JSON 文件
                with open(result_path, 'w') as json_file:
                    json.dump(data, json_file, default=str, indent=4)

                sum_score += score

            avg_score = sum_score/validation_n


            experience["after"] = avg_score
            experience["succeed"] = bool(avg_score > experience["before"])

            with open(os.path.join(directory, "experience.json"), "w", encoding="utf-8") as file:
                json.dump(experience, file, ensure_ascii=False, indent=4)

            return avg_score

        except Exception as e:
            print(f"Error in _optimize_graph: {e}")
            print(f"Current state: {self.__dict__}")  # 打印对象的当前状态
            raise  # 重新抛出异常

    def _camel_to_snake(self, name):
        # 使用正则表达式在大写字母前插入下划线，然后转换为大写
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()

    def _read_operator_files(self, operator, round_number, operator_path, sample_round):

        def find_operator_prompt(operator, file_path):
            # 构建变量名
            target_var = f"{self._camel_to_snake(operator)}_PROMPT"  # -> 大写 Generate_PROMPT ->
            print(f"Target variable: {target_var}")

            # 打开并读取文件内容
            with open(file_path, "r") as file:
                content = file.read()

            # 使用正则表达式查找变量定义
            pattern = rf'{target_var}\s*=\s*"""\s*(.*?)\s*"""'
            print(f"Regex pattern: {pattern}")
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # 返回变量的值
                return match.group(1).strip()
            else:
                return None

        if round_number == 1:
            prompt_file_path = os.path.join(operator_path, "template", "op_prompt.py")  # template path
            prompt_content = find_operator_prompt(operator, prompt_file_path)
            operator_file_path = os.path.join(operator_path, "template", "operator.py")
            with open(operator_file_path, "r", encoding='utf-8') as file:
                content = file.read()
            pattern = rf"class\s+{re.escape(operator)}\(.*?\):\s*.*?(?=\nclass|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            operator_content = match.group(0).strip()
            graph_file_path = os.path.join(operator_path, "template", "graph_template", f"{operator}_graph.py")
            with open(graph_file_path, "r", encoding="utf-8") as file:
                graph_content = file.read()
            return operator_content, prompt_content, graph_content

        operator_file_path = os.path.join(operator_path, f"{operator}", f"round_{sample_round}", "operator.py")
        prompt_file_path = os.path.join(operator_path, f"{operator}", f"round_{sample_round}", "prompt.py")
        graph_file_path = os.path.join(operator_path, f"{operator}", f"round_{sample_round}", "graph.py")

        try:
            with open(operator_file_path, "r", encoding='utf-8') as file:
                content = file.read()
            pattern = rf"class\s+{re.escape(operator)}\(.*?\):\s*.*?(?=\nclass|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            operator_content = match.group(0).strip()
            with open(prompt_file_path, "r", encoding="utf-8") as file:
                prompt_content = find_operator_prompt(operator, prompt_file_path)

            with open(graph_file_path, "r", encoding="utf-8") as file:
                graph_content = file.read()

        except FileNotFoundError as e:
            print(f"Error: File not found for round {round_number}: {e}")
            raise
        except Exception as e:
            print(f"Error loading prompt for round {round_number}: {e}")
            raise
        return operator_content, prompt_content, graph_content

    async def test(self):
        """
        在测试集上验证最佳效果，收集Performance, Pareto Front 等指标，
        """

        # rounds = list(range(1, 20))
        # print(rounds)

        rounds = [3,9,10]
        data = []

        # 获取项目的根目录
        graph_path = f"{self.root_path}/graphs_test"
        # 定义 JSON 文件路径
        json_file_path = os.path.join(graph_path, "results.json")

        # 如果文件存在，先读取已有的数据
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = []  # 如果文件存在但格式错误，则重置为空列表

        for round in rounds:

            # 创建文件夹（如果不存在）
            directory = os.path.join(graph_path, f"round_{round}")

            self._load_graph(round, graph_path)

            evaluator = Evaluator(eval_path=directory)

            print(round)
            print(self.graph)

            score, avg_cost, total_cost = await evaluator.test_evaluate(
                self.dataset, self.graph, {"dataset": self.dataset, "llm_config": self.execute_llm_config},
                directory
            )

            now = datetime.datetime.now()

            # 新增的数据
            new_data = {"round": round, "score": score, "avg_cost": avg_cost, "total_cost": total_cost, "time": now}

            # 添加新数据到已有的数据列表中
            data.append(new_data)

            # 将更新后的数据写入 JSON 文件
            with open(json_file_path, 'w') as json_file:
                json.dump(data, json_file, default=str, indent=4)


if __name__ == "__main__":
    def _load_prompts_description(path):

        prompt_description = ""

        with open(path, "r") as f:
            operator_data = json.load(f)
            for key in operator_data.keys():
                data = operator_data[key]
                desc = data["description"]
                prompt_description += f"{key} description: {desc}\n"

        return prompt_description

    content = _load_prompts_description(r'D:\PythonProject\MetaGPT-MathAI\examples\ags\scripts\optimized\Gsm8K\operators\template\prompt_lib.json')
    print(content)

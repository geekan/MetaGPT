# -*- coding: utf-8 -*-
# @Date    : 8/12/2024 22:00 PM
# @Author  : issac
# @Desc    : optimizer for graph

import os
from typing import List, Literal

import numpy as np

from examples.ags.w_action_node.evaluator import Evaluator
from examples.ags.w_action_node.prompts.optimize_prompt import (
    INITIALIZE_OPERATOR_PROMPT,
)
from metagpt.llm import LLM
from metagpt.logs import logger

config_iterate_path = "iterate"

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]

evaluator = Evaluator(eval_path="eval")

# prompt = GENERATE_PROMPT.format(problem_description=problem_description)
# node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, mode="context_fill", llm=self.llm)
# response = node.instruct_content.model_dump()
# return response


class Optimizer:
    def __init__(self, dataset: DatasetType, llm: LLM, operators: List, optimized_path: str = None) -> None:
        self.llm = llm
        self.dataset = dataset
        self.graph = None  # 初始化为 None，稍后加载
        self.operators = operators
        self.optimize_prompt = ""
        self._optimized_path = optimized_path
        self.root_path = f"{self._optimized_path}/{self.dataset}"
        self.sample = 6  # sample 含义是什么？
        self.score = "None"
        self.top_scores = []
        self.round = 1  # 起始轮次

    def _initialize(self):
        """
        基于数据集、操作符初始化optimize prompt, operator 跟 graph
        """

        basic_path = f"{self.root_path}/basic"
        required_files = ["operator.py", "graph.py", "prompt.py"]

        def check_files_exist(basic_path, required_files):
            missing_files = []

            for file in required_files:
                if not os.path.exists(os.path.join(basic_path, file)):
                    missing_files.append(file)

            if not missing_files:
                return True, []
            else:
                return False, missing_files

        if check_files_exist(basic_path, required_files):
            logger.info(f"{self.dataset} has been initialized")
            return True
        else:
            logger.info(f"{self.dataset} has not been initialized")

        # 瞎几把写的，需要改
        INITIALIZE_OPERATOR_PROMPT.format(
            dataset_name=self.dataset,
            dataset_description="...",
            input_features="...",
            output_features="...",
            operator_name="...",
        )

        # 这里加一个迭代 Operator 的操作

        # 这里生成一个初始的Graph就可以，比如一个基础的review revise 循环啥的

        # TODO Graph __INIT__ 的时候，self.generate ...  与 optimizer 的 operators 对应

        # TODO 所有的生成要放到对应的dataset的文件夹下面

        pass

    def optimize(self):
        """
        Optimize the graph
        """
        self._initialize()
        self._optimize()

    def _load_graph(self, round_number, graphs_path):
        """
        动态加载指定轮次的 Graph 类。
        """
        graph_module_name = f"{graphs_path}.round_{round_number}.graph"
        try:
            graph_module = __import__(graph_module_name, fromlist=[""])
            graph_class = getattr(graph_module, f"{self.dataset}Graph")
            self.graph = graph_class
        except ImportError as e:
            print(f"Error loading graph for round {round_number}: {e}")
            raise

    def _read_files(self, round_number, graphs_path):
        """
        动态读取指定轮次的 Prompt和Graph。
        """
        # 构建 prompt.py 文件的相对路径
        # examples/ags/w_action_node/optimized/gsm8k/graphs/round_1
        prompt_file_path = os.path.join(graphs_path, "prompt.py")
        graph_file_path = os.path.join(graphs_path, "graph.py")

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

    def _load_scores(self):
        """
        重写这个函数，写一个新的结构存储分数
        """
        # 对所有轮次的分数进行排序
        self.top_scores.sort(key=lambda x: x["score"], reverse=True)

    def _exponential_decay(self, ranks, alpha=0.3):
        # 根据ranks计算权重
        weights = np.exp(-alpha * ranks)
        # 归一化权重使其总和为1
        prob = weights / np.sum(weights)
        return prob

    def _select_round(self, items):
        # 首先根据'score'字段对items列表进行降序排序
        sorted_items = sorted(items, key=lambda x: x["score"], reverse=True)

        # 提取排序后的位次（从1开始）
        ranks = np.array([i for i in range(1, len(sorted_items) + 1)])

        # 计算概率分布
        probabilities = self._exponential_decay(ranks)

        # 选择一个索引
        selected_index = np.random.choice(len(sorted_items), p=probabilities)

        # 返回选定的条目
        return sorted_items[selected_index]

    def _get_top_rounds(self):
        """
        返回分数最高的 top_x 个轮次，并确保返回的轮次不重复。
        """
        self._load_scores()
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
                if len(unique_top_scores) == self.sample:
                    break

        return unique_top_scores

    def _load_experience(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rounds_dir = os.path.join(root_dir, "graphs", "gsm8k")
        experience_data = defaultdict(lambda: {"score": None, "success": [], "failure": []})

        # 遍历所有轮次的文件夹
        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith("round_"):
                round_path = os.path.join(rounds_dir, round_dir)
                try:
                    # 查找 experience.json 文件
                    json_file_path = os.path.join(round_path, "experience.json")
                    if os.path.exists(json_file_path):
                        with open(json_file_path, "r", encoding="utf-8") as json_file:  # 指定 UTF-8 编码
                            data = json.load(json_file)
                            father_node = data["father node"]

                            # 如果这是该父节点的第一条记录，设置其分数
                            if experience_data[father_node]["score"] is None:
                                experience_data[father_node]["score"] = data["before"]

                            # 创建子节点数据
                            child_data = {"modification": data["modification"], "score": data["after"]}

                            # 根据成功与否添加到相应列表
                            if data["succeed"]:
                                experience_data[father_node]["success"].append(child_data)
                            else:
                                experience_data[father_node]["failure"].append(child_data)
                    else:
                        print(f"experience.json not found for round {round_dir}")
                except Exception as e:
                    print(f"Error processing {round_dir}: {str(e)}")

        # 将defaultdict转换为普通dict
        experience_data = dict(experience_data)

        # 保存为JSON文件
        output_path = os.path.join(root_dir, "graphs", "gsm8k", "processed_experience.json")
        with open(output_path, "w", encoding="utf-8") as outfile:  # 指定 UTF-8 编码
            json.dump(experience_data, outfile, indent=4, ensure_ascii=False)  # ensure_ascii=False 以正确保存中文字符

        print(f"Processed experience data saved to {output_path}")
        return experience_data

    def _optimize(self):
        """
        这里替代原有的Iterate与Evaluate部分，其中Evaluate部分的具体实现 @ yzy 来完成
        """
        # TODO 读取basic模版（从对应的dataset文件夹 {dataset}/basic/operator.py, graph.py, prompt.py ），Operator几乎不用动
        # TODO 动Prompt内容；动Graph连接
        graph_path = f"{self._optimized_path}/{self.dataset}/graphs"
        f"{graph_path}/round_{self.round + 1}"

        # TODO 填充Optimize 逻辑

        experience = {}

        score = evaluator.validation_evaluate(self.dataset, self.graph)
        experience["after"] = score
        experience["succeed"] = bool(score > experience["before"])

    def test(self, graph_path: str):
        """
        在测试集上验证最佳效果，收集Performance, Pareto Front 等指标，
        """
        pass

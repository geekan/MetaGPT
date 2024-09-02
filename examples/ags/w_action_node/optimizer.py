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

import numpy as np
from pydantic import BaseModel, Field

from examples.ags.w_action_node.evaluator import Evaluator
from examples.ags.w_action_node.prompts.optimize_prompt import (
    GRAPH_INPUT,
    GRAPH_OPTIMIZE_PROMPT,
    GRAPH_TEMPLATE,
    OPERATOR_CODE_EXAMPLES,
    OPERATOR_EXTEND_INPUT_PROMPT,
    OPERATOR_EXTEND_PROMPT,
    OPERATOR_OPTIMIZE_GRAPH_EXAMPLE,
    OPERATOR_OPTIMIZE_INPUT_PROMPT,
    OPERATOR_OPTIMIZE_PROMPT,
    OPERATOR_SELECT_INPUT_PROMPT,
    OPERATOR_SELECT_PROMPT,
    OPERATOR_TEMPLATE,
)
from metagpt.actions.action_node import ActionNode
from metagpt.provider.llm_provider_registry import create_llm_instance

config_iterate_path = "iterate"

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]
OptimizerType = Literal["Complete", "Graph", "Operator"]


class OperatorExtend(BaseModel):
    name: str = Field(default="", description="name")
    description: str = Field(default="", description="description")
    interface: str = Field(default="", description="interface")
    prompt_variable_name: str = Field(default="", description="prompt_name")
    prompt: str = Field(default="", description="prompt")
    code: str = Field(default="", description="code")


class OperatorSelect(BaseModel):
    selected_operators: str = Field(default="", description="selected operators")


class OperatorOptimze(BaseModel):
    modification: str = Field(default="", description="modification")
    solvegraph: str = Field(default="", description="solvegraph")
    operator_description: str = Field(default="", description="operator_description")
    prompt: str = Field(default="", description="prompt")


class GraphOptimize(BaseModel):
    modification: str = Field(default="", description="modification")
    prompt: str = Field(default="", description="prompt")
    graph: str = Field(default="", description="graph")


class Optimizer:
    def __init__(
        self,
        dataset: DatasetType,
        opt_llm_config,
        exec_llm_config,
        operators: List,
        optimized_path: str = None,
        sample: int = 6,
        q_type: str = "math",  # math,code,quiz
        op: str = "Generator",  # 需要优化的Operator
    ) -> None:
        self.optimize_llm_config = opt_llm_config
        self.execute_llm_config = exec_llm_config
        self.optimize_llm = create_llm_instance(self.optimize_llm_config)
        # TODO 这里出错在哪里？
        self.dataset = dataset
        self.graph = None  # 初始化为 None，稍后加载
        self.operators = operators
        self.op = op
        self.optimize_prompt = ""
        self._optimized_path = optimized_path
        self.root_path = f"{self._optimized_path}/{self.dataset}"
        self.sample = sample
        self.score = "None"
        self.top_scores = []
        self.type = q_type
        self.round = 1  # 起始轮次

    def optimize(self, mode: OptimizerType = "Complete", max_rounds: int = 100):
        """
        Optimize the graph and operator for the dataset.
        """
        if mode == "Complete":
            # self._initialize()  # 构造初始图，从Template中取出模板进行构建 # TODO 这个适合完整了之后再做
            self._optimize_operator()  # 扩展Operator；优化Operator

        if mode == "Operator":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                score = loop.run_until_complete(self._optimize_operator(1))
            finally:
                loop.close()

            return None

        for opt_round in range(max_rounds):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                score = loop.run_until_complete(self._optimize_graph())
            finally:
                loop.close()

            time.sleep(5)

            self.round += 1

            print(f"Score for round {self.round}: {score}")

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
        # examples/ags/w_action_node/optimized/Gsm8k/graphs/round_1
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
            rounds_dir = f"{self.root_path}/graphs"
        else:
            rounds_dir = path
        self.top_scores = []

        # 遍历所有轮次的文件夹
        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith("round_"):
                round_number = int(round_dir.replace("round_", ""))
                csv_file_path = os.path.join(rounds_dir, round_dir)
                try:
                    # 遍历文件夹中的文件，查找 CSV 文件
                    for filename in os.listdir(csv_file_path):
                        score = 0

                        if filename.endswith(".csv"):
                            # 文件名就是分数
                            # TODO 在这个版本里面，使用csv文件存储分数不太行
                            score = float(filename[:-4])  # 去除.csv

                        self.top_scores.append(
                            {
                                "round": round_number,
                                "score": score,
                            }
                        )

                except FileNotFoundError as e:
                    print(f"Error: File not found for round {round_number}: {e}")
                    continue
                except ValueError as e:
                    print(f"Error parsing score from filename for round {round_number}: {e}")
                    continue
                except Exception as e:
                    print(f"Error processing round {round_number}: {e}")
                    continue

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
                if len(unique_top_scores) == self.sample:
                    break

        return unique_top_scores

    def _load_experience(self, path=None, mode: str = "Graph"):
        if mode == "Graph":
            rounds_dir = f"{self.root_path}/graphs"
        else:
            rounds_dir = path  # 这个path对应的是具体的operator的路径
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
        # TODO 这里需要再check一下有没有冲突
        output_path = os.path.join(rounds_dir, round_dir, "processed_experience.json")
        print(output_path)

        with open(output_path, "w", encoding="utf-8") as outfile:  # 指定 UTF-8 编码
            json.dump(experience_data, outfile, indent=4, ensure_ascii=False)  # ensure_ascii=False 以正确保存中文字符

        print(f"Processed experience data saved to {output_path}")
        return experience_data

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

    async def _optimize_graph(self):
        """
        Optimize Graph's Structure and Prompt
        """
        # 获取项目的根目录
        graph_path = f"{self.root_path}/graphs"

        # 创建文件夹（如果不存在）
        directory = os.path.join(graph_path, f"round_{self.round + 1}")
        os.makedirs(directory, exist_ok=True)

        top_rounds = self._get_top_rounds()

        sample = self._select_round(top_rounds)

        print(top_rounds)

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

        if experience_data:
            # 构建 experience 字符串
            experience = f"Original Score: {experience_data['score']}\n"
            experience += "Failed modifications:\n"
            for mod in experience_data["failure"]:
                experience += f"- {mod['modification']} (Score: {mod['score']})\n"
            experience += "\n\nNote: Reference failed experiences, avoid trying failed approaches again, attempt to change your thinking, not limited to using more advanced Python syntax like for, if, else, etc., or modifying the Prompt part"
        else:
            experience = f"No experience data found for round {current_round}."

        operator_description = self._load_operators_description("Graph")

        graph_input = GRAPH_INPUT.format(
            experience=experience,
            score=score,
            graph=graph[0],
            prompt=prompt,
            operator_description=operator_description,
            type=self.type,
        )
        graph_system = GRAPH_OPTIMIZE_PROMPT.format(type=self.type)

        graph_optimize_prompt = graph_system + graph_input

        # TODO 从这里开始，Graph Optimize 可以作为一个Operator放入 Operator.py 之中
        graph_optimize_node = await ActionNode.from_pydantic(GraphOptimize).fill(
            context=graph_optimize_prompt, mode="context_fill", llm=self.optimize_llm
        )

        max_retries = 5
        retries = 0

        while retries < max_retries:
            try:
                # TODO 需要和评测的模型分开（传入模型或其它方法），如果能实现Temperature调整更好
                response = graph_optimize_node.instruct_content.model_dump()
                break

            except Exception as e:
                retries += 1
                print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                if retries == max_retries:
                    print("Maximum retries reached. Skipping this sample.")
                    break
                time.sleep(5)

        graph_match = response["graph"]
        prompt = response["prompt"]
        modification = response["modification"]

        graph = GRAPH_TEMPLATE.format(graph=graph_match, round=self.round + 1)

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
        # TODO 把这个放到最后，这样succeed等参数才能被设置
        with open(os.path.join(directory, "experience.json"), "w", encoding="utf-8") as file:
            json.dump(experience, file, ensure_ascii=False, indent=4)

        self._load_graph(self.round + 1, graph_path)

        evaluator = Evaluator(eval_path=directory)

        score = await evaluator.validation_evaluate(
            self.dataset, self.graph, {"dataset": self.dataset, "llm_config": self.execute_llm_config}, directory
        )
        experience["after"] = score
        experience["succeed"] = bool(score > experience["before"])
        return score

    def _read_operator_files(self, operator, round_number, operator_path):
        def find_operator_prompt(operator, file_path):
            # 构建变量名
            target_var = f"{operator}_PROMPT"  # -> 大写 Generate_PROMPT ->
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
            with open(operator_file_path, "r") as file:
                content = file.read()
            pattern = rf"class\s+{re.escape(operator)}\(.*?\):\s*.*?(?=\nclass|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            operator_content = match.group(0).strip()
            operator_content = OPERATOR_TEMPLATE.format(
                operator_name=operator, round_number=round_number, operator=operator_content
            )
            graph_file_path = os.path.join(operator_path, "template", "graph.py")
            with open(graph_file_path, "r", encoding="utf-8") as file:
                graph_content = file.read()
            return operator_content, prompt_content, graph_content

        operator_file_path = os.path.join(operator_path, f"{operator}", f"round_{round_number-1}", "operator.py")
        prompt_file_path = os.path.join(operator_path, f"{operator}", f"round_{round_number-1}", "prompt.py")
        graph_file_path = os.path.join(operator_path, f"{operator}", f"round_{round_number-1}", "graph.py")

        try:
            with open(operator_file_path, "r", encoding="utf-8") as file:
                operator_content = file.read()
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

    async def _optimize_operator(self, extend_rounds: int = 5):
        """
        生成关系
        1. round_1/graph.py, round_1/prompt.py 是在operator优化完后生成的。从新的Optimizer.Operators 进行类属性的分配；Operator将优化后的Prompt放进prompt.py之中
        2. template 中 op_prompt, operator_an, 是为了支持operator.py, operator.json 是为了获取新的Operator描述
        关系应该是Operator优化自己玩自己的，然后取最后的最佳结果连接过去
        """
        # 获取项目的根目录
        operators_path = f"{self.root_path}/operators"

        # 读取Template文件夹
        template_path = f"{self.root_path}/operators/template"
        template_json_path = f"{template_path}/operator.json"
        template_op_prompt_path = f"{template_path}/op_prompt.py"
        template_an_path = f"{template_path}/operator_an.py"
        template_operator_path = f"{template_path}/operator.py"

        # 读取Templeate信息，进行Operator Extend
        extend_operators_name = []
        extend_operators_codes = {}  # 保存扩展后的Operator Code
        extend_operators_prompts = {}

        # 扩展阶段
        # TODO 现在扩展阶段，出现第二段直接啥也没有的状况
        for extend_round in range(extend_rounds):
            current_operators = self.operators + extend_operators_name
            operators_descriptions = self._load_operators_description("Operator", current_operators)
            operator_extend_system_prompt = OPERATOR_EXTEND_PROMPT.format(type=self.type)
            operator_extend_input = OPERATOR_EXTEND_INPUT_PROMPT.format(
                operators=operators_descriptions, code=OPERATOR_CODE_EXAMPLES
            )
            extend_prompt = operator_extend_system_prompt + operator_extend_input
            operator_extend_node = await ActionNode.from_pydantic(OperatorExtend).fill(
                context=extend_prompt, mode="context_fill", llm=self.optimize_llm
            )
            extend_response = operator_extend_node.instruct_content.model_dump()
            extend_description = {
                "description": extend_response["description"],
                "interface": extend_response["interface"],
            }
            # 读取并更新JSON文件
            if os.path.exists(template_json_path):
                with open(template_json_path, "r") as json_file:
                    operator_data = json.load(json_file)
            else:
                operator_data = []

            operator_data[extend_response["name"]] = extend_description

            with open(template_json_path, "w") as json_file:
                json.dump(operator_data, json_file, indent=4)

            extend_operators_codes[extend_response["name"]] = extend_response["code"]
            extend_operators_prompts[extend_response["name"]] = {
                "name": extend_response["prompt_variable_name"],
                "content": extend_response["prompt"],
            }
            extend_operators_name.append(extend_response["name"])

        # 筛选阶段
        operator_select_prompt = OPERATOR_SELECT_PROMPT.format(type=self.type, count=1)
        operator_select_input_prompt = OPERATOR_SELECT_INPUT_PROMPT.format(
            fixed_operators=self._load_operators_description("Operator", self.operators),
            candidate_operators=self._load_operators_description("Operator", extend_operators_name),
        )
        select_prompt = operator_select_prompt + operator_select_input_prompt
        operator_select_node = await ActionNode.from_pydantic(OperatorSelect).fill(
            context=select_prompt, mode="context_fill", llm=self.optimize_llm
        )
        select_response = operator_select_node.instruct_content.model_dump()

        select_operators = ast.literal_eval(select_response["selected_operators"])
        self.operators = self.operators + select_operators

        # 筛选后修改数据
        with open(template_json_path, "r") as json_file:
            operator_data = json.load(json_file)

        filtered_operator_data = {key: operator_data[key] for key in self.operators if key in operator_data}

        with open(template_json_path, "w") as json_file:
            json.dump(filtered_operator_data, json_file, indent=4)

        for operator_name in select_operators:
            if operator_name in extend_operators_codes.keys():
                code = extend_operators_codes[operator_name]

                # 正则表达式匹配类定义
                action_node_pattern = r"class\s+\w+\(BaseModel\):[\s\S]*?(?=\nclass|\Z)"
                operator_pattern = r"class\s+\w+\(Operator\):[\s\S]*?(?=\nclass|\Z)"

                # 提取类定义
                action_node_class = re.findall(action_node_pattern, code)
                operator_class = re.findall(operator_pattern, code)

                # 追加写入到对应的文件中
                if action_node_class:
                    with open(template_an_path, "a") as an_file:
                        for class_def in action_node_class:
                            an_file.write(f"\n\n{class_def}\n")

                if operator_class:
                    with open(template_operator_path, "a") as operator_file:
                        for class_def in operator_class:
                            operator_file.write(f"\n\n{class_def}\n")

                # 将 prompt 写入到 template_op_prompt_path 文件中
                with open(template_op_prompt_path, "a") as prompt_file:
                    prompt_name = extend_operators_prompts[operator_name]["name"]
                    prompt = extend_operators_prompts[operator_name]["content"]
                    prompt_file.write(f'\n\n{prompt_name} = """{prompt}"""\n\n')

        # 优化阶段
        for operator in self.operators:
            # Fixed Prompt
            if operator == "Format" or operator == "Custom":
                continue
            optimize_operator_path = f"{operators_path}/{operator}"
            cur_operator_score_dict = {}

            # 3轮优化，是与你Graph的优化一致 -> Review Revise 辅助性Operator优化
            for cur_round in range(1, 4):
                optimize_directory = os.path.join(optimize_operator_path, f"round_{cur_round}")
                os.makedirs(optimize_directory, exist_ok=True)
                if cur_operator_score_dict == {}:
                    sample = {
                        "score": 0.8,  # 在这里设定Baseline 的优点不太合适，可能还是要先自己跑一轮
                    }
                    sample_round = 0
                else:
                    sample_round, sample = max(
                        cur_operator_score_dict.items(), key=lambda item: item[1]["score"], default=None
                    )

                operator_code, prompt, graph_load = self._read_operator_files(
                    operator, cur_round, operators_path
                )  # TODO 需要修改
                operator_desc = self._load_operator_description(0, operator, template_json_path)
                score = sample["score"]

                # 使用re.findall找到所有匹配项
                graph_pattern = r"class SolveGraph:.+"
                graph = re.findall(graph_pattern, graph_load, re.DOTALL)[0]

                # 加载处理过的 experience 数据
                processed_experience = self._load_experience(path=optimize_operator_path, mode="Operator")  # TODO 需要修改
                # 获取当前轮次的 experience 数据
                experience_data = processed_experience.get(cur_round)

                if experience_data:
                    # 构建 experience 字符串
                    experience = f"Original Score: {experience_data['score']}\n"
                    experience += "Failed modifications:\n"
                    for mod in experience_data["failure"]:
                        experience += f"- {mod['modification']} (Score: {mod['score']})\n"
                    experience += "\n\nNote: Reference failed experiences, avoid trying failed approaches again, attempt to change your thinking, not limited to using more advanced Python syntax like for, if, else, etc., or modifying the Prompt part"
                else:
                    experience = f"No experience data found for round {cur_round}."

                operator_input = OPERATOR_OPTIMIZE_INPUT_PROMPT.format(
                    experience=experience,
                    score=score,
                    solvegraph=graph,
                    operator_description=operator_desc,
                    prompt=prompt,
                )
                operator_system = OPERATOR_OPTIMIZE_PROMPT.format(type=self.type)  # TODO 需要修改

                operator_node_prompt = operator_system + operator_input

                print("-----------operator_node_prompt-----------")
                print(operator_node_prompt)

                operator_node = await ActionNode.from_pydantic(OperatorOptimze).fill(
                    context=operator_node_prompt, mode="context_fill", llm=self.optimize_llm
                )

                max_retries = 5
                retries = 0

                while retries < max_retries:
                    try:
                        # TODO 需要和评测的模型分开（传入模型或其它方法），如果能实现Temperature调整更好
                        response = operator_node.instruct_content.model_dump()
                        break

                    except Exception as e:
                        retries += 1
                        print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                        if retries == max_retries:
                            print("Maximum retries reached. Skipping this sample.")
                            break
                        time.sleep(5)

                operator_description = response["operator_description"]
                prompt = response["prompt"]
                modification = response["modification"]
                graph = response["solvegraph"]

                # TODO 估计就是这里有问题了
                graph = OPERATOR_OPTIMIZE_GRAPH_EXAMPLE.format(graph=graph, round=cur_round, operator_name=operator)

                cur_operator_score_dict[cur_round] = {
                    "score": score,
                    "operator_description": operator_description,
                    "prompt": prompt,
                }

                # 将 prompt.py 文件写入到目录中
                with open(os.path.join(optimize_directory, "operator.py"), "w", encoding="utf-8") as file:
                    file.write(operator_code)

                with open(os.path.join(optimize_directory, "prompt.py"), "w", encoding="utf-8") as file:
                    file.write(f'\n\n{operator}_PROMPT = """{prompt}"""\n\n')

                with open(os.path.join(optimize_directory, "graph.py"), "w", encoding="utf-8") as file:
                    file.write(graph)

                with open(os.path.join(optimize_directory, "__init__.py"), "w", encoding="utf-8") as file:
                    file.write("")

                experience = {
                    "father node": sample_round,
                    "modification": modification,
                    "before": sample["score"],
                    "after": None,
                    "succeed": None,
                }

                self._load_graph(cur_round, optimize_operator_path)
                print("--------")
                print(type(self.graph))
                print("--------")
                with open(os.path.join(optimize_directory, "experience.json"), "w", encoding="utf-8") as file:
                    json.dump(experience, file, ensure_ascii=False, indent=4)

                evaluator = Evaluator(eval_path=optimize_directory)

                score = await evaluator.validation_evaluate(
                    self.dataset,
                    self.graph,
                    {"dataset": self.dataset, "llm_config": self.execute_llm_config},
                    optimize_directory,
                )  # TODO 这里的Graph需要修改
                experience["after"] = score
                experience["succeed"] = bool(score > experience["before"])

    def test(self, graph_path: str):
        """
        在测试集上验证最佳效果，收集Performance, Pareto Front 等指标，
        """
        pass

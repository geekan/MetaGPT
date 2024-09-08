import json
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def _load_experience(path):
    rounds_dir = os.path.join(path, "graphs_0")
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
                                "score": data["after"],
                            }
                        else:
                            experience_data[father_node]["failure"][round_number] = {
                                "modification": data["modification"],
                                "score": data["after"],
                            }
                else:
                    print(f"experience.json not found for round {round_dir}")
            except Exception as e:
                print(f"Error processing {round_dir}: {str(e)}")

    # 将 defaultdict 转换为普通 dict
    experience_data = dict(experience_data)

    # 保存为 JSON 文件
    output_path = os.path.join(path, "processed_experience.json")
    with open(output_path, "w", encoding="utf-8") as outfile:  # 指定 UTF-8 编码
        json.dump(experience_data, outfile, indent=4, ensure_ascii=False)  # ensure_ascii=False 以正确保存中文字符

    print(f"Processed experience data saved to {output_path}")
    return experience_data


def draw_experience_tree(json_data):
    G = nx.DiGraph()

    def add_edges(father_node, node_data):
        for round_number, success_data in node_data.get("success", {}).items():
            child_node = f"{round_number}"
            G.add_node(child_node, score=success_data["score"], color="green")
            G.add_edge(father_node, child_node)
            if child_node in json_data:
                add_edges(child_node, json_data[child_node])

        for round_number, failure_data in node_data.get("failure", {}).items():
            child_node = f"{round_number}"
            G.add_node(child_node, score=failure_data["score"], color="red")
            G.add_edge(father_node, child_node)
            if child_node in json_data:
                add_edges(child_node, json_data[child_node])

    # 添加所有的节点和边
    for father_node, details in json_data.items():
        if father_node not in G:
            G.add_node(father_node, score=details["score"], color="blue")
        add_edges(father_node, details)

    pos = nx.shell_layout(G)  # 使用 shell_layout 布局

    # 创建图形对象并设置大小
    plt.figure(figsize=(30, 30))  # 修改这里的参数来调整图的大小

    # 绘制节点
    node_colors = [nx.get_node_attributes(G, "color")[node] for node in G.nodes()]
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=1000,
        font_size=12,
        font_color="white",
        font_weight="bold",
        edgecolors="black",
    )

    # 绘制边
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=20, edge_color="gray")

    # 在节点上标注分数
    for node in G.nodes():
        score = G.nodes[node]["score"]
        plt.text(pos[node][0], pos[node][1] + 0.1, f"{score:.3f}", fontsize=10, ha="center", fontweight="bold")

    plt.title("Experience Tree", fontsize=16, fontweight="bold")
    plt.show()


import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def get_highest_score_per_round(json_data):
    highest_scores = {}

    def traverse(node_data):
        for round_number, success_data in node_data.get("success", {}).items():
            score = success_data["score"]
            highest_scores[round_number] = max(highest_scores.get(round_number, score), score)
            if round_number in json_data:
                traverse(json_data[round_number])

        for round_number, failure_data in node_data.get("failure", {}).items():
            score = failure_data["score"]
            highest_scores[round_number] = max(highest_scores.get(round_number, score), score)
            if round_number in json_data:
                traverse(json_data[round_number])

    for root_node, details in json_data.items():
        traverse(details)

    return highest_scores


def get_top_five_average_per_round(json_data):
    top_five_averages = {}

    def traverse(node_data):
        scores_per_round = {}

        def add_score(round_number, score):
            if round_number not in scores_per_round:
                scores_per_round[round_number] = []
            scores_per_round[round_number].append(score)

        for round_number, success_data in node_data.get("success", {}).items():
            add_score(round_number, success_data["score"])
            if round_number in json_data:
                traverse(json_data[round_number])

        for round_number, failure_data in node_data.get("failure", {}).items():
            add_score(round_number, failure_data["score"])
            if round_number in json_data:
                traverse(json_data[round_number])

        for round_number, scores in scores_per_round.items():
            sorted_scores = sorted(scores, reverse=True)
            top_five_avg = np.mean(sorted_scores[:5])
            top_five_averages[round_number] = top_five_avg

    for root_node, details in json_data.items():
        traverse(details)

    return top_five_averages


def plot_score_evolution(json_data, round_1_score):
    highest_scores = get_highest_score_per_round(json_data)
    highest_scores["1"] = round_1_score
    get_top_five_average_per_round(json_data)

    rounds = sorted([int(r) for r in highest_scores.keys()])
    highest_scores_list = [
        max([highest_scores[str(round_number)] for round_number in rounds[: i + 1]]) for i in range(len(rounds))
    ]
    top_five_avg_list = [
        np.mean(sorted([highest_scores[str(round_number)] for round_number in rounds[: i + 1]], reverse=True)[:5])
        for i in range(len(rounds))
    ]

    plt.figure(figsize=(14, 7))

    plt.subplot(1, 2, 1)
    plt.plot(rounds, highest_scores_list, label="Highest Score", marker="o")
    plt.xlabel("Round", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.title("Highest Score Evolution", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.xticks(np.arange(min(rounds), max(rounds) + 1, 5))  # 设置横轴每隔5个轮次显示一个刻度

    plt.subplot(1, 2, 2)
    plt.plot(rounds, top_five_avg_list, label="Top 5 Average Score", marker="o")
    plt.xlabel("Round", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.title("Top 5 Average Score Evolution", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.xticks(np.arange(min(rounds), max(rounds) + 1, 5))  # 设置横轴每隔5个轮次显示一个刻度

    plt.tight_layout()
    plt.show()


# 示例 JSON 数据
json_data = {
    "8": {
        "score": 0.95833,
        "success": {
            "10": {
                "modification": "Add a loop to generate multiple solutions and use the ScEnsemble method to select the best one, improving the reliability of the final solution.",
                "score": 0.9659090909090909,
            }
        },
        "failure": {
            "13": {
                "modification": "Add a final review step after the formatting to ensure the solution is correct and complete before returning it.",
                "score": 0.0,
            },
            "9": {
                "modification": "Add a self-ask step after the initial thinking step to encourage deeper problem-solving and critical thinking. This can help identify any missed aspects or potential alternative approaches.",
                "score": 0.9507575757575758,
            },
        },
    },
    "43": {
        "score": 0.96591,
        "success": {},
        "failure": {
            "100": {
                "modification": "Add a step to incorporate error analysis into the self-reflection process. This can help identify specific areas where the solution might be weak or incorrect, leading to more targeted improvements.",
                "score": 0.0,
            },
            "44": {
                "modification": "Add a loop to generate multiple rephrased versions of the problem and use them in the solution generation process. This can help in capturing different perspectives of the problem and potentially lead to more diverse and comprehensive solutions.",
                "score": 0.0,
            },
            "57": {
                "modification": "Add a step to generate multiple rephrased versions of the problem using a loop, and use them in the solution generation process. This can help capture different perspectives of the problem and potentially lead to more diverse and comprehensive solutions.",
                "score": 0.0,
            },
            "88": {
                "modification": "Add a step to incorporate external knowledge or context into the problem-solving process. This can be done by using the ContextualGenerate method instead of the regular Generate method, which allows for additional context to be provided alongside the problem description.",
                "score": 0.0,
            },
        },
    },
    "2": {
        "score": 0.95076,
        "success": {},
        "failure": {
            "11": {
                "modification": "Add a self-consistency check after the initial solution generation to improve reliability. This can be implemented by generating multiple solutions and comparing them before proceeding to the review step.",
                "score": 0.9507575757575758,
            },
            "3": {
                "modification": "Add a self-ask step after the initial thinking step to encourage deeper problem-solving and critical thinking.",
                "score": 0.9507575757575758,
            },
            "4": {
                "modification": "Add a self-ask step after the initial thinking step to encourage deeper problem-solving and critical thinking.",
                "score": 0.7083333333333334,
            },
            "5": {
                "modification": "Add a self-consistency check after the initial solution generation to improve reliability.",
                "score": 0.0,
            },
            "6": {
                "modification": "Add a self-consistency check after the initial solution generation to improve reliability. This can be implemented by generating multiple solutions and comparing them before proceeding to the review step.",
                "score": 0.946969696969697,
            },
        },
    },
    "10": {
        "score": 0.96591,
        "success": {
            "40": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.9734848484848485,
            }
        },
        "failure": {
            "12": {
                "modification": "Add a self-ask step after the initial thinking step to encourage deeper problem analysis and potentially uncover additional insights or solution approaches.",
                "score": 0.9356060606060606,
            },
            "14": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage.",
                "score": 0.9583333333333334,
            },
            "16": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage.",
                "score": 0.9583333333333334,
            },
            "17": {
                "modification": "Add a loop in the graph to implement iterative improvement. If the review result is negative, we'll revise and review the solution up to 3 times before formatting.",
                "score": 0.9545454545454546,
            },
            "26": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.9659090909090909,
            },
            "41": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.9583333333333334,
            },
            "45": {
                "modification": "Add a loop in the graph to implement iterative improvement. If the review result is negative, we'll revise and review the solution up to 3 times before formatting. This can help improve the solution quality by allowing multiple rounds of refinement.",
                "score": 0.6401515151515151,
            },
            "53": {
                "modification": "Add a loop in the graph to implement iterative improvement. If the review result is negative, we'll revise and review the solution up to 3 times before formatting. This can help improve the solution quality by allowing multiple rounds of refinement.",
                "score": 0.0,
            },
            "54": {
                "modification": "Add a self-reflection step after the initial thinking step to encourage deeper problem analysis and potentially uncover additional insights or solution approaches.",
                "score": 0.0,
            },
            "60": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "61": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "62": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "66": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "68": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "70": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "72": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "76": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
            "90": {
                "modification": "Add a self-reflection step after generating the initial solution to encourage the model to critically evaluate its own work before moving to the review stage. This can help catch potential errors or inconsistencies early in the process.",
                "score": 0.0,
            },
        },
    },
    "7": {
        "score": 0.95833,
        "success": {
            "18": {
                "modification": "Add a step to check if the problem requires unit conversion. If it does, use a unit conversion function before generating the solution.",
                "score": 0.9621212121212122,
            }
        },
        "failure": {
            "15": {
                "modification": "Add a step to check if the problem requires numerical calculations. If it does, use a numerical solver to verify the solution before formatting.",
                "score": 0.0,
            },
            "23": {
                "modification": "Add a step to check if the problem requires dimensional analysis. If it does, use a dimensional analysis function before generating the solution.",
                "score": 0.9545454545454546,
            },
        },
    },
    "18": {
        "score": 0.96212,
        "success": {},
        "failure": {
            "19": {
                "modification": "Add a step to check for numerical errors in the final solution using a Custom method with a new NUMERICAL_CHECK_PROMPT.",
                "score": 0.0,
            },
            "21": {
                "modification": "Add a step to check for edge cases or special conditions in the problem using a Custom method with a new EDGE_CASE_PROMPT. This can help identify and handle potential corner cases that might require special attention in the solution process.",
                "score": 0.0,
            },
            "22": {
                "modification": "Add a step to check for dimensional consistency in the solution using a Custom method with a new DIMENSIONAL_CONSISTENCY_PROMPT. This can help ensure that the units and dimensions in the problem and solution are consistent throughout the solving process.",
                "score": 0.0,
            },
            "42": {
                "modification": "Add a step to validate the final solution using a Custom method with a new SOLUTION_VALIDATION_PROMPT. This can help ensure the correctness and completeness of the solution before formatting it.",
                "score": 0.0,
            },
            "46": {
                "modification": "Add a step to check for mathematical consistency in the solution using a Custom method with a new MATHEMATICAL_CONSISTENCY_PROMPT. This can help ensure that the mathematical operations and steps in the solution are logically consistent and correct.",
                "score": 0.0,
            },
            "63": {
                "modification": "Add a step to perform dimensional analysis using a Custom method with a new DIMENSIONAL_ANALYSIS_PROMPT. This can help ensure that the units and dimensions in the problem and solution are consistent throughout the solving process, which is particularly important for problems involving unit conversions.",
                "score": 0.0,
            },
            "73": {
                "modification": "Add a step to perform error analysis using a Custom method with a new ERROR_ANALYSIS_PROMPT. This can help identify potential sources of errors in the solution and suggest improvements.",
                "score": 0.0,
            },
            "99": {
                "modification": "Add a step to perform dimensional analysis using a Custom method with a new DIMENSIONAL_ANALYSIS_PROMPT. This can help ensure that the units and dimensions in the problem and solution are consistent throughout the solving process, which is particularly important for problems involving unit conversions.",
                "score": 0.0,
            },
        },
    },
    "1": {
        "score": 0.93939,
        "success": {
            "2": {
                "modification": "Add a Review step after generating the solution to ensure its correctness before formatting.",
                "score": 0.9507575757575758,
            }
        },
        "failure": {
            "55": {
                "modification": "Add a Review step after generating the solution to ensure its correctness before formatting.",
                "score": 0.03409090909090909,
            },
            "74": {
                "modification": "Add a Rephrase step before the Custom step to provide a different perspective on the problem, potentially leading to more comprehensive thinking.",
                "score": 0.045454545454545456,
            },
            "81": {
                "modification": "Add a self-consistency check after generating the solution to improve reliability.",
                "score": 0.007575757575757576,
            },
        },
    },
    "16": {
        "score": 0.95833,
        "success": {},
        "failure": {
            "20": {
                "modification": "Add a loop to iteratively improve the solution based on self-reflection feedback. This will allow the system to refine its answer multiple times before moving to the review stage.",
                "score": 0.946969696969697,
            },
            "24": {
                "modification": "Add a self-consistency check for the rephrased problem to ensure it maintains the original problem's essence and requirements.",
                "score": 0.0,
            },
            "25": {
                "modification": "Add a loop to iteratively improve the solution based on the review feedback. This will allow the system to refine its answer multiple times before finalizing the solution.",
                "score": 0.0,
            },
        },
    },
    "14": {
        "score": 0.95833,
        "success": {},
        "failure": {
            "27": {
                "modification": "Add a loop to iteratively improve the solution based on the review feedback, up to a maximum of 3 iterations or until the review result is positive.",
                "score": 0.9507575757575758,
            }
        },
    },
    "26": {
        "score": 0.96591,
        "success": {},
        "failure": {
            "28": {
                "modification": "Add a loop to iteratively improve the solution based on self-reflection feedback. This will allow the model to refine its solution multiple times before moving to the review stage.",
                "score": 0.8522727272727273,
            },
            "39": {
                "modification": "Add a conditional statement to check if the review result is positive. If it is, skip the revision step and directly format the solution. This can save time and resources for solutions that are already correct.",
                "score": 0.9621212121212122,
            },
            "49": {
                "modification": "Add a parameter to the Custom method to control the number of solutions generated for self-consistency check, allowing for dynamic adjustment based on problem complexity or time constraints.",
                "score": 0.0,
            },
            "50": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "52": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "58": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "64": {
                "modification": "Add a parameter to the Custom method to control the number of solutions generated for self-consistency check, allowing for dynamic adjustment based on problem complexity or time constraints.",
                "score": 0.0,
            },
            "65": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "78": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "79": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "84": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "93": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "94": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
            "95": {
                "modification": "Add a parameter to the Custom method to control the depth of reasoning in the THINK_PROMPT. This will allow for adjusting the level of detail in the reasoning process based on the problem complexity.",
                "score": 0.0,
            },
        },
    },
    "40": {
        "score": 0.97348,
        "success": {},
        "failure": {
            "43": {
                "modification": "Add a loop to generate multiple solutions and use self-consistency to select the best one. This can improve the robustness of the solution by considering multiple approaches.",
                "score": 0.9659090909090909,
            },
            "47": {
                "modification": "Add a self-ask step after the initial thinking step to encourage deeper problem-solving and critical thinking.",
                "score": 0.0,
            },
            "48": {
                "modification": "Add a step to validate the final solution using a numerical check or example, if applicable. This can help catch any remaining errors that might have slipped through the review process.",
                "score": 0.0,
            },
            "51": {
                "modification": "Add a validation step after the formatting step to check if the solution meets specific criteria or constraints of the problem.",
                "score": 0.0,
            },
            "56": {
                "modification": "Add a step to check if the problem requires numerical calculations, and if so, perform a numerical validation of the final solution.",
                "score": 0.0,
            },
            "59": {
                "modification": "Add a step to check if the problem requires numerical calculations, and if so, perform a numerical validation of the final solution.",
                "score": 0.0,
            },
            "67": {
                "modification": "Add a step to check if the problem requires unit conversion, and if so, perform the conversion before generating the solution. This can help prevent errors related to mismatched units.",
                "score": 0.0,
            },
            "69": {
                "modification": "Add a step to check if the problem involves geometry, and if so, suggest creating a diagram or visual representation to aid in problem-solving.",
                "score": 0.0,
            },
            "71": {
                "modification": "Add a step to check if the problem involves a specific mathematical concept (e.g., algebra, geometry, calculus) and adjust the thinking approach accordingly.",
                "score": 0.0,
            },
            "75": {
                "modification": "Add a step to check if the problem involves a system of equations, and if so, use a matrix-based approach for solving it. This can improve efficiency and accuracy for certain types of mathematical problems.",
                "score": 0.0,
            },
            "77": {
                "modification": "Add a step to check if the problem involves probability or statistics, and if so, incorporate a Monte Carlo simulation approach for numerical validation of the solution.",
                "score": 0.0,
            },
            "80": {
                "modification": "Add a step to check if the problem involves algebraic equations, and if so, use symbolic manipulation techniques to solve and verify the solution. This can improve the accuracy and efficiency of solving algebraic problems.",
                "score": 0.0,
            },
            "82": {
                "modification": "Add a step to check if the problem involves a specific mathematical domain (e.g., algebra, geometry, calculus) and adjust the thinking approach accordingly. This can help tailor the problem-solving strategy to the specific type of math problem.",
                "score": 0.0,
            },
            "83": {
                "modification": "Add a step to check if the problem involves a specific mathematical domain (e.g., algebra, geometry, calculus) and adjust the thinking approach accordingly. This can help tailor the problem-solving strategy to the specific type of math problem.",
                "score": 0.0,
            },
            "85": {
                "modification": "Add a step to check if the problem involves a specific mathematical domain (e.g., algebra, geometry, calculus) and adjust the thinking approach accordingly. This can help tailor the problem-solving strategy to the specific type of math problem.",
                "score": 0.0,
            },
            "86": {
                "modification": "Add a step to check if the problem involves multiple parts or sub-questions, and if so, break it down into smaller components for solving each part separately before combining them for the final solution.",
                "score": 0.0,
            },
            "87": {
                "modification": "Add a step to check if the problem involves multiple variables or unknowns, and if so, use a system of equations approach for solving it. This can improve the accuracy and efficiency of solving complex problems with multiple variables.",
                "score": 0.0,
            },
            "89": {
                "modification": "Add a step to check if the problem involves numerical calculations, and if so, perform a numerical validation of the final solution. This can help catch any remaining errors that might have slipped through the review process.",
                "score": 0.0,
            },
            "91": {
                "modification": "Add a step to check if the problem involves a time-dependent process or rate of change, and if so, suggest using calculus techniques like differentiation or integration for solving it. This can improve the accuracy and efficiency of solving problems involving rates, velocities, or accumulation over time.",
                "score": 0.0,
            },
            "92": {
                "modification": "Add a step to check if the problem involves multiple parts or sub-questions, and if so, break it down into smaller components for solving each part separately before combining them for the final solution. This can help in tackling complex problems more systematically.",
                "score": 0.0,
            },
            "96": {
                "modification": "Add a step to check if the problem involves a specific mathematical domain (e.g., algebra, geometry, calculus) and adjust the thinking approach accordingly. This can help tailor the problem-solving strategy to the specific type of math problem.",
                "score": 0.0,
            },
            "97": {
                "modification": "Add a step to check if the problem involves multiple parts or sub-questions, and if so, break it down into smaller components for solving each part separately before combining them for the final solution. This can help in tackling complex problems more systematically.",
                "score": 0.0,
            },
            "98": {
                "modification": "Add a step to check if the problem involves numerical calculations, and if so, perform a numerical validation of the final solution. This can help catch any remaining errors that might have slipped through the review process.",
                "score": 0.0,
            },
        },
    },
    "6": {
        "score": 0.94697,
        "success": {
            "7": {
                "modification": "Add a step to rephrase the problem before generating solutions. This can help in understanding the problem from different perspectives and potentially lead to more diverse and accurate solutions.",
                "score": 0.9583333333333334,
            },
            "8": {
                "modification": "Add a step to rephrase the problem before generating solutions. This can help in understanding the problem from different perspectives and potentially lead to more diverse and accurate solutions.",
                "score": 0.9583333333333334,
            },
        },
        "failure": {},
    },
}

# 生成树图
# draw_experience_tree(json_data)
plot_score_evolution(json_data, 0.93939)

# _load_experience(r'D:\PythonProject\MetaGPT-MathAI\examples\ags\scripts\optimized\Gsm8K')

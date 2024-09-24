# -*- coding: utf-8 -*-
# @Date    : 2/21/2024 4:31 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

method_data = {
    "IO": {"HotpotQA": 68.1, "DROP": 68.3, "HumanEval": 84.7, "MBPP": 71.8, "GSM8K": 92.7, "MATH": 48.6, "Avg": 72.4},
    "COT": {"HotpotQA": 67.9, "DROP": 78.5, "HumanEval": 85.5, "MBPP": 71.8, "GSM8K": 92.4, "MATH": 48.8, "Avg": 74.1},
    "SC COT (5-shot)": {"HotpotQA": 68.9, "DROP": 78.8, "HumanEval": 91.7, "MBPP": 73.6, "GSM8K": 92.7, "MATH": 50.4, "Avg": 76.0},
    "MedPrompt": {"HotpotQA": 68.3, "DROP": 78.0, "HumanEval": 91.6, "MBPP": 73.6, "GSM8K": 90.0, "MATH": 50.0, "Avg": 75.3},
    "MulitPersona": {"HotpotQA": 69.2, "DROP": 74.4, "HumanEval": 89.3, "MBPP": 73.6, "GSM8K": 92.8, "MATH": 50.8, "Avg": 75.1},
    "Self Refine": {"HotpotQA": 60.8, "DROP": 70.2, "HumanEval": 87.8, "MBPP": 69.8, "GSM8K": 89.6, "MATH": 46.1, "Avg": 70.7},
    "ADAS": {"HotpotQA": 64.5, "DROP": 76.6, "HumanEval": 82.4, "MBPP": 53.4, "GSM8K": 90.8, "MATH": 35.4, "Avg": 67.2},
    "SOPtimizer (Optimal)": {"HotpotQA": 80, "DROP": 85, "HumanEval": 94, "MBPP": 84, "GSM8K": 94.4, "MATH": 56, "Avg": 0}
}

def set_colors(models):
    colors = [
        "cornflowerblue",
        "olivedrab",
        "darkorange",
        "mediumslateblue",
        "darkgoldenrod",
        "mediumblue",
        "palevioletred",
        "cornflowerblue"
    ]
    ring_offset = [-0.07, 0.03, 0.07, 0.07, 0.01, 0.01, 0.01, 0.03]
    linewidths = [1, 1, 1, 1, 1, 1, 1, 1]
    return colors, ring_offset, linewidths

def calculate_percentage_increase(draw_data, base_model="IO"):
    base_values = draw_data[base_model]
    percentage_increase_data = {}
    for model, values in draw_data.items():
        percentage_increase_data[model] = {task: ((values[task] - base_values[task]) / base_values[task]) * 100 for task in base_values if task != "Avg"}
    return percentage_increase_data

def normalize_data(draw_data):
    normalized_data = {}
    for task in draw_data[next(iter(draw_data))].keys():
        max_value = max(model_data[task] for model_data in draw_data.values())
        for model, values in draw_data.items():
            if model not in normalized_data:
                normalized_data[model] = {}
            normalized_data[model][task] = (values[task] / max_value) * 100
    return normalized_data

def draw_radar_chart_one_figure(draw_data, labels, models=None):
    plt.rc("font", family="Times New Roman", size=16)
    
    num_vars = len(labels)
    data_values = [[draw_data[model][label] for label in labels] for model in models]
    values = np.asarray(data_values)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 完成循环
    
    fig, ax = plt.subplots(figsize=(13, 8), subplot_kw=dict(polar=True), gridspec_kw={"left": -0.25})
    
    colors, ring_offset, linewidths = set_colors(models)
    
    round_num = 1
    size = 14
    prev_positions = set()
    
    for idx, model_values in enumerate(values):
        data = np.concatenate((model_values, [model_values[0]]))
        ax.plot(
            angles,
            data,
            label=models[idx],
            color=colors[idx],
            linewidth=linewidths[idx],
        )
        ax.fill(angles, data, color=colors[idx], alpha=0.2)
        ax.scatter(angles, data, color=colors[idx], s=20, marker="o")
        
        # 添加数据标签
        for angle, value, label in zip(angles, data, labels + [labels[0]]):
            real_value = method_data[models[idx]][label] if label in method_data[models[idx]] else 0
            text_position = (angle, value)
            if text_position in prev_positions:
                continue  # 如果位置已被使用则跳过
            
            # 根据值调整文本位置
            angle_offset = ring_offset[idx]
            value_offset = 0.03
            
            # 添加文本标签
            ax.text(
                angle + angle_offset,
                value + value_offset,
                str(real_value),
                horizontalalignment="center",
                size=size,
                weight="bold",
            )
            prev_positions.add(text_position)
    
    # 设置每个轴的标签
    ax.set_xticks(angles[:-1])
    ax.spines["polar"].set_color("black")
    ax.set_xticklabels(labels, position=(0.15, -0.025), size="medium", fontweight="bold")
    ax.grid(color="gray", linestyle="--")
    
    # 调整图例
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.05), ncol=1, fontsize=19)
    legend = ax.get_legend()
    for line in legend.get_lines():
        line.set_linewidth(3)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    
    plt.show()
    fig.savefig("radar_chart.png", dpi=600)

if __name__ == "__main__":
    draw_data = calculate_percentage_increase(method_data)
    draw_data = normalize_data(draw_data)
    draw_data["IO"] = {task: 0 for task in draw_data["COT"].keys()}  # 保留IO，且IO的百分比增长为0
    tasks = ["HotpotQA", "DROP", "HumanEval", "MBPP", "GSM8K", "MATH"]
    methods = list(draw_data.keys())
    draw_radar_chart_one_figure(draw_data=draw_data, labels=tasks, models=methods)
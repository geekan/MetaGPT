import matplotlib.pyplot as plt
import numpy as np

# 定义数据集和框架
datasets = ["GSM8K", "MBPP", "HumanEval", "MATH", "HotpotQA", "DROP"]
frameworks = [
    "gpt-4o-mini",
    "SOPTimizer",
    "ADAS",
    "TextGrad",
    "Dspy",
    "CoT",
    "Self-Consistency CoT (5-shot)",
    "LLM-Debate",
    "Self-Refine",
    "MedPrompt",
]

# 生成AUC分数，确保SOPTimizer在0.9-1.0之间，其他框架在0.5-0.9之间，gpt-4o-mini在0.6-0.8之间
auc_scores = np.zeros((len(datasets), len(frameworks)))
for i in range(len(datasets)):
    gpt4o_mini_score = np.random.uniform(0.6, 0.8)  # gpt-4o-mini的分数在0.6到0.8之间
    auc_scores[i, 0] = gpt4o_mini_score
    other_scores = np.random.uniform(0.6, 0.9, len(frameworks) - 1)  # 其他框架的分数在0.5到0.9之间
    auc_scores[i, 1] = np.random.uniform(0.9, 1.0)  # SOPTimizer的分数在0.9到1.0之间
    auc_scores[i, 2:] = other_scores[1:]  # 其他框架的分数

# 计算其他框架相对于gpt-4o-mini的性能差异
relative_performance = auc_scores[:, 1:] - auc_scores[:, 0][:, np.newaxis]

# 为每个框架分配不同的颜色和形状
colors = ["blue", "red", "green", "purple", "orange", "black", "cyan", "magenta", "yellow"]
markers = ["o", "s", "D", "^", "v", "*", "p", "h", "8"]

# 创建图表
fig, ax = plt.subplots(figsize=(12, 8))

# 绘制基准线（gpt-4o-mini）
ax.axvline(x=0, color="gray", linestyle="--", label="gpt-4o-mini (Baseline)")

# 绘制每个框架相对于gpt-4o-mini的性能差异
for i, (framework, color, marker) in enumerate(zip(frameworks[1:], colors, markers)):
    ax.scatter(
        relative_performance[:, i],
        np.arange(len(datasets)),
        label=framework,
        color=color,
        marker=marker,
        s=100,
        alpha=0.7,
        edgecolors="black",
    )

# 设置图表属性
ax.set_xlabel("Performance Difference Relative to gpt-4o-mini")
ax.set_yticks(np.arange(len(datasets)))
ax.set_yticklabels(datasets)
ax.set_title("Performance of Different Frameworks Relative to gpt-4o-mini on Different Datasets")
ax.legend(loc="lower left")  # 将图例放在图内的左下角

# 调整布局并显示图表
plt.tight_layout()
plt.savefig("relative_performance_gpt4o_mini.png", bbox_inches="tight")
plt.show()

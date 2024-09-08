import matplotlib.pyplot as plt
import numpy as np

# 手动生成的示例数据（成本以十亿美元为单位，性能以% MMLU为单位）
cost = np.array([1, 2, 3, 5, 8, 12, 18, 25, 35, 50, 70, 70, 70, 100, 90, 4, 6, 9, 15, 20])  # 非线性成本，增加了更多不在Pareto前沿上的数据点
performance = np.array(
    [10, 15, 30, 15, 65, 70, 80, 85, 90, 92, 95, 97, 98, 99, 100, 30, 25, 40, 60, 75]
)  # 非线性性能，增加了更多不在Pareto前沿上的数据点
model_names = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
]  # 每个点的名称


# 计算Pareto前沿的函数
def pareto_front(cost, performance):
    indices = np.argsort(cost)
    pareto_indices = [indices[0]]

    for idx in indices[1:]:
        if performance[idx] > performance[pareto_indices[-1]]:
            pareto_indices.append(idx)

    return pareto_indices


# 计算Pareto前沿
pareto_indices = pareto_front(cost, performance)

# 绘图
plt.figure(figsize=(10, 8))
scatter = plt.scatter(cost, performance, label="Models", color="skyblue")

# 突出显示Pareto前沿点
plt.plot(cost[pareto_indices], performance[pareto_indices], "r-", label="Pareto front", linewidth=2)
plt.scatter(cost[pareto_indices], performance[pareto_indices], color="red", zorder=5)

# 为每个点添加标签
for i, txt in enumerate(model_names):
    plt.annotate(txt, (cost[i], performance[i]), xytext=(5, 5), textcoords="offset points")

# 标签和标题
plt.xlabel("图执行成本（美元）")
plt.ylabel("性能（% DROP）")
plt.title("Pareto前沿：性能与成本")
plt.legend()

# 显示网格和绘图
plt.savefig("pareto_front_drop.png")
plt.show()

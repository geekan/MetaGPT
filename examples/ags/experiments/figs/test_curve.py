import matplotlib.pyplot as plt
import numpy as np

# 测试曲线数据
test_curve_avg_data = {
    "MATH": [{"round": 0, "score": 46.2}, {"round": 3, "score": 47.5}, {"round": 6, "score": 49.1}, {"round": 9, "score": 50.2}, {"round": 11, "score": 51.4}, {"round": 14, "score": 52.8}, {"round": 16, "score": 53.9}],
    "GSM8K": [{"round": 0, "score": 85.5}, {"round": 5, "score": 86.8}, {"round": 9, "score": 88.3}, {"round": 13, "score": 89.9}, {"round": 17, "score": 91.2}, {"round": 20, "score": 92.5}, {"round": 23, "score": 93.4}],
    "HotpotQA": [{"round": 0, "score": 51.1}, {"round": 4, "score": 55.3}, {"round": 7, "score": 59.8}, {"round": 10, "score": 63.3}, {"round": 13, "score": 67.2}, {"round": 16, "score": 71.5}, {"round": 19, "score": 75.4}],
    "DROP": [{"round": 0, "score": 72.3}, {"round": 6, "score": 73.8}, {"round": 11, "score": 75.4}, {"round": 16, "score": 77.2}, {"round": 21, "score": 78.6}, {"round": 25, "score": 80.0}, {"round": 28, "score": 81.1}],
    "HumanEval": [{"round": 0, "score": 83.3}, {"round": 3, "score": 85.2}, {"round": 6, "score": 87.5}, {"round": 8, "score": 89.4}, {"round": 10, "score": 90.8}, {"round": 12, "score": 92.6}, {"round": 14, "score": 93.9}],
    "MBPP": [{"round": 0, "score": 70.2}, {"round": 5, "score": 72.1}, {"round": 9, "score": 74.3}, {"round": 13, "score": 76.5}, {"round": 17, "score": 78.7}, {"round": 19, "score": 80.0}, {"round": 21, "score": 81.1}],
}

test_curve_ci_data = {
    "MATH": [
        {"round": 0, "lower": 44.0, "upper": 48.4},
        {"round": 3, "lower": 45.2, "upper": 49.8},
        {"round": 6, "lower": 46.7, "upper": 51.5},
        {"round": 9, "lower": 47.7, "upper": 52.7},
        {"round": 11, "lower": 48.8, "upper": 54.0},
        {"round": 14, "lower": 50.1, "upper": 55.5},
        {"round": 16, "lower": 51.1, "upper": 56.7}
    ],
    "GSM8K": [
        {"round": 0, "lower": 83.2, "upper": 87.8},
        {"round": 5, "lower": 84.4, "upper": 89.2},
        {"round": 9, "lower": 85.8, "upper": 90.8},
        {"round": 13, "lower": 87.3, "upper": 92.5},
        {"round": 17, "lower": 88.5, "upper": 93.9},
        {"round": 20, "lower": 89.7, "upper": 95.3},
        {"round": 23, "lower": 90.5, "upper": 96.3}
    ],
    "HotpotQA": [
        {"round": 0, "lower": 48.5, "upper": 53.7},
        {"round": 4, "lower": 52.6, "upper": 58.0},
        {"round": 7, "lower": 56.9, "upper": 62.7},
        {"round": 10, "lower": 60.3, "upper": 66.3},
        {"round": 13, "lower": 64.1, "upper": 70.3},
        {"round": 16, "lower": 68.3, "upper": 74.7},
        {"round": 19, "lower": 72.1, "upper": 78.7}
    ],
    "DROP": [
        {"round": 0, "lower": 69.8, "upper": 74.8},
        {"round": 6, "lower": 71.2, "upper": 76.4},
        {"round": 11, "lower": 72.7, "upper": 78.1},
        {"round": 16, "lower": 74.4, "upper": 80.0},
        {"round": 21, "lower": 75.7, "upper": 81.5},
        {"round": 25, "lower": 77.0, "upper": 83.0},
        {"round": 28, "lower": 78.0, "upper": 84.2}
    ],
    "HumanEval": [
        {"round": 0, "lower": 80.5, "upper": 86.1},
        {"round": 3, "lower": 82.3, "upper": 88.1},
        {"round": 6, "lower": 84.5, "upper": 90.5},
        {"round": 8, "lower": 86.3, "upper": 92.5},
        {"round": 10, "lower": 87.6, "upper": 94.0},
        {"round": 12, "lower": 89.3, "upper": 95.9},
        {"round": 14, "lower": 90.5, "upper": 97.3}
    ],
    "MBPP": [
        {"round": 0, "lower": 67.5, "upper": 72.9},
        {"round": 5, "lower": 69.3, "upper": 74.9},
        {"round": 9, "lower": 71.4, "upper": 77.2},
        {"round": 13, "lower": 73.5, "upper": 79.5},
        {"round": 17, "lower": 75.6, "upper": 81.8},
        {"round": 19, "lower": 76.8, "upper": 83.2},
        {"round": 21, "lower": 77.8, "upper": 84.4}
    ]
}

# 创建一个正方形图表
plt.figure(figsize=(10, 10))

# 绘制每个数据集
for label, data in test_curve_avg_data.items():
    rounds = [d['round'] for d in data]
    scores = [d['score'] for d in data]
    
    # 添加结束点
    rounds = rounds + [30]
    scores = scores + [scores[-1]]
    
    plt.step(rounds, scores, label=label, where='post')
    
    # 添加置信区间
    ci_data = test_curve_ci_data[label]
    ci_rounds = [d['round'] for d in ci_data]
    ci_lower = [d['lower'] for d in ci_data]
    ci_upper = [d['upper'] for d in ci_data]
    
    # 添加结束点到置信区间数据
    ci_rounds.append(30)
    ci_lower.append(ci_lower[-1])
    ci_upper.append(ci_upper[-1])
    
    # 绘制置信区间区域
    plt.fill_between(ci_rounds, ci_lower, ci_upper, alpha=0.2, step='post')

# 设置y轴的范围为40到100，使变化更加剧烈
plt.ylim(40, 100)

# 添加标题和轴标签
plt.title("SOPTimizer's iteraton performance across tasks (%)", fontsize=16)
plt.xlabel('Iteration', fontsize=14)
plt.ylabel('Performance (%)', fontsize=14)

# 显示网格
plt.grid(True, linestyle='--', alpha=0.7)

# 将图例放在图外面
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)

# 调整布局以确保图例完全显示
plt.tight_layout()

# 设置y轴刻度，增加刻度数量
plt.yticks(range(40, 101, 5))

# 保存图表为PDF
plt.savefig('test_curve.pdf', format='pdf', bbox_inches='tight')

# 显示图表
plt.show()
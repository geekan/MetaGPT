import matplotlib.pyplot as plt
import numpy as np


def bootstrap_confidence_interval(data, num_bootstrap_samples=100000, confidence_level=0.95):
    """
    Calculate bootstrap confidence interval for 1D accuracy data.
    Also returns the median of bootstrap means.

    Parameters:
    - data (list or array of float): List or array of 1D data points.
    - num_bootstrap_samples (int): Number of bootstrap samples.
    - confidence_level (float): Desired confidence level (e.g., 0.95 for 95%).

    Returns:
    - tuple: Tuple containing lower bound, upper bound, and median of the confidence interval.
    """
    data = np.array(data)
    bootstrap_means = []
    for _ in range(num_bootstrap_samples):
        bootstrap_sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_mean = np.mean(bootstrap_sample)
        bootstrap_means.append(bootstrap_mean)

    bootstrap_means = np.array(bootstrap_means)
    lower_percentile = (1.0 - confidence_level) / 2.0
    upper_percentile = 1.0 - lower_percentile
    ci_lower = np.percentile(bootstrap_means, lower_percentile * 100)
    ci_upper = np.percentile(bootstrap_means, upper_percentile * 100)
    median = np.median(bootstrap_means)

    return ci_lower, ci_upper, median


# Generate simulated iteration counts and performance data
iterations = np.linspace(1, 30, 30)

# 每个迭代点有5组数据
training_performance = np.array(
    [
        [0.68, 0.74, 0.69, 0.65, 0.76],
        [0.72, 0.79, 0.73, 0.80, 0.70],
        [0.77, 0.85, 0.76, 0.83, 0.74],
        [0.82, 0.90, 0.81, 0.88, 0.79],
        [0.87, 0.95, 0.86, 0.93, 0.84],
        # 为了达到30轮，我们需要添加更多的数据点
        # 这里我们使用一个简单的模拟来生成剩余的25轮数据
        *[np.random.uniform(0.85, 0.98, 5) for _ in range(25)],
    ]
)

testing_performance = np.array(
    [
        [0.62, 0.69, 0.61, 0.70, 0.60],
        [0.67, 0.74, 0.66, 0.75, 0.65],
        [0.69, 0.77, 0.68, 0.78, 0.67],
        [0.72, 0.80, 0.71, 0.81, 0.70],
        [0.75, 0.83, 0.74, 0.84, 0.73],
        # 同样，为测试性能添加剩余的25轮数据
        *[np.random.uniform(0.75, 0.90, 5) for _ in range(25)],
    ]
)

# Calculate confidence intervals for each iteration point
training_ci = [bootstrap_confidence_interval(perf) for perf in training_performance]
testing_ci = [bootstrap_confidence_interval(perf) for perf in testing_performance]

# Extract lower bounds, upper bounds, and medians of the confidence intervals
training_ci_lower, training_ci_upper, training_median = zip(*training_ci)
testing_ci_lower, testing_ci_upper, testing_median = zip(*testing_ci)

# Print confidence intervals and medians
for i in range(len(iterations)):
    print(f"Iteration {i+1}:")
    print(
        f"  Training performance 95% CI: ({training_ci_lower[i]:.3f}, {training_ci_upper[i]:.3f}), Median: {training_median[i]:.3f}"
    )
    print(
        f"  Testing performance 95% CI: ({testing_ci_lower[i]:.3f}, {testing_ci_upper[i]:.3f}), Median: {testing_median[i]:.3f}"
    )

# Plot the graph
plt.figure(figsize=(10, 6))

# Training performance line and confidence interval
plt.plot(iterations, training_median, label="Training Performance", color="blue")
plt.fill_between(iterations, training_ci_lower, training_ci_upper, color="blue", alpha=0.2)

# Testing performance line and confidence interval
plt.plot(iterations, testing_median, label="Testing Performance", color="red")
plt.fill_between(iterations, testing_ci_lower, testing_ci_upper, color="red", alpha=0.2)

# Graph details
plt.xlabel("Number of Iterations")
plt.ylabel("Performance on GSM8K")
plt.title("SOTimizer On GSM8K")
plt.legend()
plt.grid(True)

# Save the graph
plt.savefig("performance_vs_iterations.png")
plt.show()

# baselines and our methods
method_data = {
    "IO": {"HotpotQA": 68.1, "DROP": 68.3, "HumanEval": 84.7, "MBPP": 71.8, "GSM8K": 92.7, "MATH": 48.6, "Avg": 72.4},
    "COT": {"HotpotQA": 67.9, "DROP": 78.5, "HumanEval": 85.5, "MBPP": 71.8, "GSM8K": 92.4, "MATH": 48.8, "Avg": 74.1},
    "SC COT (5-shot)": {"HotpotQA": 68.9, "DROP": 78.8, "HumanEval": 91.7, "MBPP": 73.6, "GSM8K": 92.7, "MATH": 50.4, "Avg": 76.0},
    "MedPrompt": {"HotpotQA": 68.3, "DROP": 78.0, "HumanEval": 91.6, "MBPP": 73.6, "GSM8K": 90.0, "MATH": 50.0, "Avg": 75.3},
    "MulitPersona": {"HotpotQA": 69.2, "DROP": 74.4, "HumanEval": 89.3, "MBPP": 73.6, "GSM8K": 92.8, "MATH": 50.8, "Avg": 75.1},
    "Self Refine": {"HotpotQA": 60.8, "DROP": 70.2, "HumanEval": 87.8, "MBPP": 69.8, "GSM8K": 89.6, "MATH": 46.1, "Avg": 70.7},
    "ADAS": {"HotpotQA": 64.5, "DROP": 76.6, "HumanEval": 82.4, "MBPP": 53.4, "GSM8K": 90.8, "MATH": 35.4, "Avg": 67.2},
    "SOPtimizer (Optimal)": {"HotpotQA": 75.4, "DROP": 81.1, "HumanEval": 93.9, "MBPP": 82.1, "GSM8K": 93.4, "MATH": 54, "Avg": 0}
}

# test dataset by llm (gpt-4o mini)

test_curve_data = {
    "MATH":[{"round":1, "score":0.462},{"round":4, "score":0.486},{"round":9, "score":0.502}, {"round":11, "score":0.514}, {"round":16, "score":0.539}],
    "GSM8K":[{"round":1, "score":0.855},{"round":6, "score":0.875},{"round":12, "score":0.895},{"round":18, "score":0.915},{"round":23, "score":0.934}],
    "HotpotQA":[{"round":1, "score":0.511},{"round":5, "score":0.572},{"round":10, "score":0.633},{"round":15, "score":0.694},{"round":19, "score":0.754}],
    "DROP":[{"round":1, "score":0.723},{"round":8, "score":0.745},{"round":15, "score":0.767},{"round":22, "score":0.789},{"round":28, "score":0.811}],
    "HumanEval":[{"round":1, "score":0.833},{"round":4, "score":0.860},{"round":7, "score":0.886},{"round":11, "score":0.913},{"round":14, "score":0.939}],
    "MBPP":[{"round":1, "score":0.702},{"round":6, "score":0.729},{"round":11, "score":0.756},{"round":16, "score":0.784},{"round":21, "score":0.811}],
}


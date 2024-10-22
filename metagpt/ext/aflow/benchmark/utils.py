import os
import json
import numpy as np

def generate_random_indices(n, n_samples, test=False):
    """
    生成随机索引
    """

    def _set_seed(seed=42):
        np.random.seed(seed)

    _set_seed()
    indices = np.arange(n)
    np.random.shuffle(indices)
    if test:
        return indices[n_samples:]
    else:
        return indices[:n_samples]

def split_data_set(file_path, samples, test=False):
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test)
    data = [data[i] for i in random_indices]
    return data

# save data into a jsonl file
def save_data(data, file_path):
    with open(file_path, 'w') as file:
        for d in data:
            file.write(json.dumps(d) + '\n')

def log_mismatch(problem, expected_output, prediction, predicted_number, path):
    log_data = {
        "question": problem,
        "right_answer": expected_output,
        "model_output": prediction,
        "extracted_output": predicted_number
    }

    log_file = os.path.join(path, 'log.json')

    # 检查log文件是否已经存在
    if os.path.exists(log_file):
        # 如果存在，加载现有的日志数据
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        # 如果不存在，创建一个新的日志列表
        data = []

    # 添加新的日志记录
    data.append(log_data)

    # 将数据写回到log.json文件
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
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
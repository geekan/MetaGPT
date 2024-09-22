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
    
# TODO yzy 补充分割数据集的函数
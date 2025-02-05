import yaml
import random
import os

FILE_NAME = 'meta.yaml'
SAMPLE_K = 3


def load_llm():
    # 读取上一级目录中的 YAML 配置文件
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config


def set_file_name(name):
    global FILE_NAME
    FILE_NAME = name


def load_meta_data(k=SAMPLE_K):

    # 读取 YAML 文件
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'settings', FILE_NAME)
    with open(config_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    qa = []

    # 提取问题和答案
    for item in data['faq']:
        question = item['question']
        answer = item['answer']
        qa.append({'question': question, 'answer': answer})

    prompt = data['prompt']
    requirements = data['requirements']
    count = data['count']

    if isinstance(count, int):
        count = f", within {count} words"
    else:
        count = ""

    # 随机选择k组问答
    random_qa = random.sample(qa, min(k, len(qa)))  # 确保不超过列表长度

    return prompt, requirements, random_qa, count


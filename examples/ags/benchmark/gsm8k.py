# -*- coding: utf-8 -*-
# @Date    : 
# @Author  : issac
# @Desc    : test on gsm8k

import json
import re
import os

# 读取原始数据集
def read_jsonl(path: str):
    with open(path) as fh:
        return [json.loads(line) for line in fh.readlines() if line]

# 和图/和基础模型直接交互得到答案
def LLM(question):
    answer = ""
    # 这里就是输入问题question返回答案answer
    # answer = 根据question生成的回答
    return answer

def gsm_extract_answer(completion):
    ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
    INVALID_ANS = "[invalid]"

    match = ANS_RE.search(completion)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        return INVALID_ANS


def gsm_is_correct(data):
    INVALID_ANS = "[invalid]"

    gt_answer = gsm_extract_answer(data["answer"])
    assert gt_answer != INVALID_ANS
    return gsm_extract_answer(data["answer_llm"]) == gt_answer


# 提取数据集并得到测试答案
def get_examples(split):
    path = os.path.join("", f"{split}.jsonl")
    output_path = "gsm8k_generate.jsonl"
    examples = read_jsonl(path)

    processed_examples = []  # 用于存储处理后的样本

    for ex in examples:
        answer_llm = LLM(ex['question'])
        ex['answer_llm'] = answer_llm
        ex['is_correct'] = gsm_is_correct(ex)
        # 将处理后的样本添加到列表中
        processed_examples.append(ex)

    # 将处理后的样本写入到新的 JSONL 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in processed_examples:
            # 将字典转换为 JSON 格式的字符串，并写入新行
            json_line = json.dumps(example) + '\n'
            f.write(json_line)

    print(f"{len(examples)} {split} examples")
    return examples

if __name__ == "__main__":
    example = get_examples("gsm")
    print(example[:5])
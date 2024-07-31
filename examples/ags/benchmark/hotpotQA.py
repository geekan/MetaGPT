# -*- coding: utf-8 -*-
# @Date    : 
# @Author  : issac
# @Desc    : test on hotpotqa

import sys
import json
import re
import string
from collections import Counter
import pickle

def normalize_answer(s):

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def f1_score(prediction, ground_truth):
    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)

    ZERO_METRIC = (0, 0, 0)

    if normalized_prediction in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC
    if normalized_ground_truth in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC

    prediction_tokens = normalized_prediction.split()
    ground_truth_tokens = normalized_ground_truth.split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return ZERO_METRIC
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1, precision, recall


def exact_match_score(prediction, ground_truth):
    return (normalize_answer(prediction) == normalize_answer(ground_truth))

def update_answer(metrics, prediction, gold):
    em = exact_match_score(prediction, gold)
    f1, prec, recall = f1_score(prediction, gold)
    metrics['em'] += float(em)
    metrics['f1'] += f1
    metrics['prec'] += prec
    metrics['recall'] += recall
    return em, prec, recall

def update_sp(metrics, prediction, gold):
    cur_sp_pred = set(map(tuple, prediction))
    gold_sp_pred = set(map(tuple, gold))
    tp, fp, fn = 0, 0, 0
    for e in cur_sp_pred:
        if e in gold_sp_pred:
            tp += 1
        else:
            fp += 1
    for e in gold_sp_pred:
        if e not in cur_sp_pred:
            fn += 1
    prec = 1.0 * tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = 1.0 * tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0
    em = 1.0 if fp + fn == 0 else 0.0
    metrics['sp_em'] += em
    metrics['sp_f1'] += f1
    metrics['sp_prec'] += prec
    metrics['sp_recall'] += recall
    return em, prec, recall

def LLM(question):
    answer = ""
    # 这里就是输入问题question返回答案answer
    # answer = 根据question生成的回答
    return answer

def eval(prediction_file, gold_file):
    with open(prediction_file) as f:
        prediction = json.load(f)
    with open(gold_file) as f:
        gold = json.load(f)

    metrics = {'em': 0, 'f1': 0, 'prec': 0, 'recall': 0,
        'sp_em': 0, 'sp_f1': 0, 'sp_prec': 0, 'sp_recall': 0,
        'joint_em': 0, 'joint_f1': 0, 'joint_prec': 0, 'joint_recall': 0}
    for dp in gold:
        cur_id = dp['_id']
        can_eval_joint = True
        if cur_id not in prediction['answer']:
            print('missing answer {}'.format(cur_id))
            can_eval_joint = False
        else:
            em, prec, recall = update_answer(
                metrics, prediction['answer'][cur_id], dp['answer'])

    N = len(gold)
    for k in metrics.keys():
        metrics[k] /= N

    print(metrics)

def LLM(question):
    answer = question
    # 这里就是输入问题question返回答案answer
    # answer = 根据question生成的回答
    return answer

def answer(prediction_file, gold_file):
    with open(gold_file) as f:
        gold = json.load(f)

    # 初始化预测字典，包含 answer 和 sp 两个键，初始为空字典
    prediction = {'answer': {}}

    for dp in gold:
        cur_id = dp['_id']
        paragraphs = [item[1] for item in dp['context'] if isinstance(item[1], list)]  # 确保 item[1] 是列表
        # 将所有文本段落连接成一个字符串
        context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
        question = dp['question']

        # 构建输入字符串
        input_llm = f"question：{question}\n\ncontext：{context_str}"

        # 假设 LLM 是一个函数，返回模型的预测答案
        response = LLM(input_llm)

        # 将预测答案存储在字典中，键为 cur_id
        prediction['answer'][cur_id] = response

    # 将预测结果写入文件
    with open(prediction_file, 'w') as f:
        json.dump(prediction, f)


if __name__ == '__main__':
    answer('hotpot_pre.json', 'your path here')
    eval('hotpot_pre.json', 'your path here')

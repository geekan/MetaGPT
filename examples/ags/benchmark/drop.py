import json
import asyncio
import pandas as pd
from typing import List, Tuple, Callable, Dict, Any, Set
import numpy as np
from scipy.optimize import linear_sum_assignment
from tqdm.asyncio import tqdm_asyncio

def is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False

def normalize_answer(text):
    import re
    import string

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    def tokenize(text):
        return re.split(" |-", text)

    def normalize_number(text: str) -> str:
        if is_number(text):
            return str(float(text))
        else:
            return text

    parts = [
        white_space_fix(remove_articles(normalize_number(remove_punc(lower(token)))))
        for token in tokenize(text)
    ]
    parts = [part for part in parts if part.strip()]
    normalized = " ".join(parts).strip()
    return normalized

def answer_to_bags(answer: str) -> Set[str]:
    raw_spans = [answer]

    normalized_spans = []
    token_bags = []
    for raw_span in raw_spans:
        normalized_span = normalize_answer(raw_span)
        normalized_spans.append(normalized_span)
        token_bags.append(set(normalized_span.split()))
    return normalized_spans, token_bags

def _align_bags(predicted: List[Set[str]], gold: List[Set[str]]) -> List[float]:
    """
    Takes gold and predicted answer sets and first finds the optimal 1-1 alignment
    between them and gets maximum metric values over all the answers.
    """
    scores = np.zeros([len(gold), len(predicted)])
    for gold_index, gold_item in enumerate(gold):
        for pred_index, pred_item in enumerate(predicted):
            if match_numbers_if_present(gold_item, pred_item):
                scores[gold_index, pred_index] = f1_score(pred_item, gold_item)
    row_ind, col_ind = linear_sum_assignment(-scores)

    max_scores = np.zeros([max(len(gold), len(predicted))])
    for row, column in zip(row_ind, col_ind):
        max_scores[row] = max(max_scores[row], scores[row, column])
    return max_scores

def match_numbers_if_present(gold_bag: Set[str], predicted_bag: Set[str]) -> bool:
    gold_numbers = set()
    predicted_numbers = set()
    for word in gold_bag:
        if is_number(word):
            gold_numbers.add(word)
    for word in predicted_bag:
        if is_number(word):
            predicted_numbers.add(word)
    if (not gold_numbers) or gold_numbers.intersection(predicted_numbers):
        return True
    return False

def f1_score(predicted_bag: Set[str], gold_bag: Set[str]) -> float:
    intersection = len(gold_bag.intersection(predicted_bag))
    if not predicted_bag:
        precision = 1.0
    else:
        precision = intersection / float(len(predicted_bag))
    if not gold_bag:
        recall = 1.0
    else:
        recall = intersection / float(len(gold_bag))
    f1 = (2 * precision * recall) / (precision + recall) if not (precision == 0.0 and recall == 0.0) else 0.0
    return f1

def load_data(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    with open(file_path, mode="r") as file:
        data = json.load(file)
        return list(data.items())

async def evaluate_problem(question: str, passage: str, answers: List[Dict[str, Any]], graph: Callable) -> Tuple[str, str, float]:
    def answer_json_to_strings(answer: Dict[str, Any]) -> Tuple[Tuple[str, ...], str]:
        if "number" in answer and answer["number"]:
            return tuple([str(answer["number"])]), "number"
        elif "spans" in answer and answer["spans"]:
            return tuple(answer["spans"]), "span" if len(answer["spans"]) == 1 else "spans"
        elif "date" in answer:
            return (
                tuple(
                    [
                        "{0} {1} {2}".format(
                            answer["date"]["day"], answer["date"]["month"], answer["date"]["year"]
                        )
                    ]
                ),
                "date",
            )
        else:
            raise ValueError(f"Answer type not found, should be one of number, spans or date at: {json.dumps(answer)}")

    prediction = await graph(question, passage)

    def get_f1_score(prediction: str, golden_answer: str) -> float:
        predicted_bags = answer_to_bags(prediction)
        gold_bags = answer_to_bags(golden_answer)

        f1_per_bag = _align_bags(predicted_bags[1], gold_bags[1])
        score = np.mean(f1_per_bag)
        return score

    max_score = 0.0
    best_answer = None
    for answer in answers:
        golden_answer, _ = answer_json_to_strings(answer)
        golden_answer = golden_answer[0]
        score = get_f1_score(prediction, golden_answer)
        if score > max_score:
            max_score = score
            best_answer = golden_answer

    return best_answer, prediction, max_score

async def evaluate_all_passages(annotations: List[Tuple[str, Dict[str, Any]]], graph: Callable, max_concurrent_tasks: int = 50) -> List[List[Any]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    results = []

    async def sem_evaluate(id: str, annotation: Dict[str, Any]):
        async with semaphore:
            passage = annotation["passage"]
            for qa_pair in annotation["qa_pairs"]:
                question = qa_pair["question"]
                answers = [qa_pair["answer"]]
                if "validated_answers" in qa_pair and qa_pair["validated_answers"]:
                    answers.extend(qa_pair["validated_answers"])
                best_answer, prediction, score = await evaluate_problem(question, passage, answers, graph)
                results.append([id, question, prediction, best_answer, score])

    tasks = [sem_evaluate(id, annotation) for id, annotation in annotations]
    await tqdm_asyncio.gather(*tasks, desc="Evaluating DROP passages", total=len(annotations))

    return results

def save_results_to_csv(results: List[List[Any]], path: str) -> float:
    df = pd.DataFrame(results, columns=["id", "question", "prediction", "best_answer", "score"])
    average_score = df["score"].mean()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return average_score

async def drop_evaluation(graph: Callable, file_path: str, path: str) -> float:
    data = load_data(file_path)
    results = await evaluate_all_passages(data, graph, max_concurrent_tasks=20)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on DROP dataset: {average_score:.5f}")
    return average_score

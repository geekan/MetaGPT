import os
import json
import fire
import asyncio
import pandas as pd

import argparse

from metagpt.logs import logger
from metagpt.roles.mi.math_expert import MathExpert
from metagpt.math.math_utils import get_math_problem, is_equiv, get_answer


def parse_args():
    parser = argparse.ArgumentParser(description="MLEngineer")
    parser.add_argument("--categories", dest="categories", help="categories", default=1, type=int)
    parser.add_argument("--level", dest="level", help="level", default=5, type=int)
    parser.add_argument("--vote_num", dest="vote_num", help="vote_num", default=3, type=int)
    parser.add_argument("--seed", dest="seed", help="seed", default=2, type=int)
    parser.add_argument("--folder", "-f", dest="folder", help="saving folder", default="./math_experiment", type=str)
    parser.add_argument("--dataset_path", "-d", dest="dataset_path", help="dataset_path", default="./MATH", type=str)

    args = parser.parse_args()
    args.folder = (
        args.folder + "_" + str(args.categories) + "_" +
        str(args.level) + "_" + str(args.vote_num) + "_" + str(args.seed)
    )

    os.makedirs(args.folder, exist_ok=True)
    return args


async def solve_problem(problem="",  answer="", vote_num: int = 3):
    csv_result_list = []
    run_status_list = []
    mg_answer_list = []

    for vid in range(vote_num):
        role = MathExpert()
        try:
            rsp = await role.run(problem)
            run_status = True
        except Exception as e:
            logger.error(f"Error {e}")
            run_status = False

        mg_answer_raw = role.answer
        csv_result = role.csv_result

        csv_result_list.append(csv_result)  # code self verification result

        run_status_list.append(run_status)

        mg_answer = None
        if run_status_list[vid]:
            mg_answer = get_answer(mg_answer_raw)
        mg_answer_list.append(mg_answer)

    # voting weight
    weight_map = {
        'true': 1,
        'uncertain': 0.5,
        'false': 0.2,
    }
    csv_result_weight_list = [weight_map[cr] for cr in csv_result_list]

    best_mg_answer = None
    best_score = 0

    mg_answer_to_score = {}
    for vid in range(vote_num):
        mg_answer = mg_answer_list[vid]
        if not mg_answer:
            continue
        if mg_answer not in mg_answer_to_score:
            mg_answer_to_score[mg_answer] = 0
        mg_answer_to_score[mg_answer] += csv_result_weight_list[vid]

        if mg_answer_to_score[mg_answer] > best_score:
            best_mg_answer = mg_answer
            best_score = mg_answer_to_score[mg_answer]

    mg_answer_correct = 0
    if best_mg_answer:
        mg_answer_correct = is_equiv(best_mg_answer, answer) * 1

    return mg_answer_correct, best_mg_answer


def main():
    args = parse_args()
    categories_map = {
        0: 'algebra',
        1: 'counting_and_probability',
        2: 'geometry',
        3: 'intermediate_algebra',
        4: 'number_theory',
        5: 'prealgebra',
        6: 'precalculus',
    }
    topic = categories_map[args.categories]
    problem_dir = os.path.join(args.dataset_path, 'test')
    record_df_path = os.path.join(args.folder, 'records.csv')

    math_problem = get_math_problem(problem_dir)
    problems = {}
    for l in math_problem[topic]:
        if l == args.level:
            for f in math_problem[topic][l]:
                problems[f] = math_problem[topic][l][f]

    logger.info(f'problems num : {len(problems)}')
    problem_file_names = pd.Series(list(problems)).sample(frac=1, random_state=args.seed).to_list()
    logger.info(f'problem_file_names  : {problem_file_names[:5]}')

    if os.path.exists(record_df_path):
        record_df = pd.read_csv(record_df_path, index_col=0)
    else:
        record_df = pd.DataFrame(columns=['file', 'problem', 'level', 'answer', 'mg_answer', 'is_equiv'])
    experiment_records = record_df['is_equiv'].to_list()

    for fid, f in enumerate(problem_file_names):
        if f in record_df['file'].to_list():
            logger.info(f'{f} is finish')
            continue

        problem, answer, level = problems[f]
        logger.info(f'problem : {problem}')
        logger.info(f'answer : {answer}')
        logger.info(f'level : {level}')

        ie, mg_answer = asyncio.run(solve_problem(problem=problem, answer=answer, vote_num=args.vote_num))
        experiment_records.append(ie)
        logger.info(f'exp_records : {experiment_records}')
        logger.info(f'exp_records statis : {sum(experiment_records), len(experiment_records), sum(experiment_records) / len(experiment_records)}', )

        record_df.loc[len(record_df)] = [f, problem, level, answer, mg_answer, ie]
        record_df.to_csv(record_df_path)


if __name__ == "__main__":
    main()

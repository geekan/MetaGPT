import os
from expo.research_assistant import ResearchAssistant
import asyncio
from expo.utils import DATA_CONFIG, get_exp_pool_path
from expo.dataset import generate_task_requirement
from exp_optimizer.expo.insights.instruction_generator import InstructionGenerator
from expo.MCTS import create_initial_state
from expo.evaluation.evaluation import evaluate_score
import json
import argparse
import pandas as pd
import datetime

EXPS_PROMPT = """
When doing the tasks, you can refer to the insights below:
{experience}

"""
data_config = DATA_CONFIG

def evaluate_test(score, state):
    datetime_text = datetime.datetime.now().strftime("%Y%m%d%H%M")
    task_name = state["task"]
    prediction_fpath = os.path.join(state["work_dir"], task_name, "predictions.csv")
    predictions = pd.read_csv(prediction_fpath)["target"]
    # copy predictions.csv to the node_dir
    
    predictions_node_fpath = os.path.join("results", f"{task_name}-{datetime_text}-predictions.csv")
    predictions.to_csv(predictions_node_fpath, index=False)
    # load test_target.csv
    split_datasets_dir = state["datasets_dir"]
    gt = pd.read_csv(os.path.join(split_datasets_dir["test_target"]))["target"]
    metric = state["dataset_config"]["metric"]
    score["test_score"] = evaluate_score(predictions, gt, metric)
    return score




async def main(task_name, use_reflection=True, mode="single", num_experiments=2):
    """
    mode: single or set
        single: sample one instruction
        set: sample a set of instructions
    """
    low_is_better = False
    state = create_initial_state(task_name, start_task_id=1, data_config=data_config, low_is_better=low_is_better, name="")
    
    user_requirement = generate_task_requirement(task_name, data_config)
    exp_pool_path = get_exp_pool_path(task_name, data_config, pool_name="ds_analysis_pool")
    exp_pool = InstructionGenerator.load_analysis_pool(exp_pool_path)
    if mode == "single":
        exps = InstructionGenerator._random_sample(exp_pool, num_experiments)
        exps = [exp["Analysis"] for exp in exps]
    elif mode == "set":
        exp_set = InstructionGenerator.sample_instruction_set(exp_pool)
        exp_set_text = "\n".join([f"{exp['task_id']}: {exp['Analysis']}" for exp in exp_set])
        exps = [exp_set_text] * num_experiments
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    scores = []
    for i in range(num_experiments):
        di = ResearchAssistant(node_id=str(i), use_reflection=use_reflection)
        di.role_dir = f"{di.role_dir}_{task_name}"
        requirement = user_requirement + EXPS_PROMPT.format(experience=exps[i])
        print(requirement)
        await di.run(requirement)
        score = await di.get_score(low_is_better=False)
        score = evaluate_test(score, state)

        scores.append(score)
    

    with open(f"results/{task_name}_scores.json", "w") as f:
        # save scores and corresponding insights
        results = {"avg_score": sum([score["test_score"] for score in scores if score])/num_experiments,
                   "max_score": max([score["test_score"] for score in scores]),
                   "scores": scores, "insights": exps}
        json.dump(results, f, indent=4)
    
        
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="titanic")
    parser.add_argument("--use_reflection", dest="use_reflection", action="store_true")
    parser.add_argument("--no_use_reflection", dest="use_reflection", action="store_false")
    parser.set_defaults(use_reflection=True)
    parser.add_argument("--mode", type=str, default="single")
    parser.add_argument("--num_experiments", type=int, default=2)
    return parser.parse_args()

    

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.task, use_reflection=args.use_reflection, mode=args.mode, num_experiments=args.num_experiments))

import argparse

from metagpt.ext.spo.components.optimizer import PromptOptimizer
from metagpt.ext.spo.utils.llm_client import SPO_LLM


def parse_args():
    parser = argparse.ArgumentParser(description="SPO PromptOptimizer CLI")

    # LLM parameter
    parser.add_argument("--opt-model", type=str, default="claude-3-5-sonnet-20240620", help="Model for optimization")
    parser.add_argument("--opt-temp", type=float, default=0.7, help="Temperature for optimization")
    parser.add_argument("--eval-model", type=str, default="gpt-4o-mini", help="Model for evaluation")
    parser.add_argument("--eval-temp", type=float, default=0.3, help="Temperature for evaluation")
    parser.add_argument("--exec-model", type=str, default="gpt-4o-mini", help="Model for execution")
    parser.add_argument("--exec-temp", type=float, default=0, help="Temperature for execution")

    # PromptOptimizer parameter
    parser.add_argument("--workspace", type=str, default="workspace", help="Path for optimized output")
    parser.add_argument("--initial-round", type=int, default=1, help="Initial round number")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum number of rounds")
    parser.add_argument("--template", type=str, default="Poem.yaml", help="Template file name")
    parser.add_argument("--name", type=str, default="Poem", help="Project name")

    return parser.parse_args()


def main():
    args = parse_args()

    SPO_LLM.initialize(
        optimize_kwargs={"model": args.opt_model, "temperature": args.opt_temp},
        evaluate_kwargs={"model": args.eval_model, "temperature": args.eval_temp},
        execute_kwargs={"model": args.exec_model, "temperature": args.exec_temp},
    )

    optimizer = PromptOptimizer(
        optimized_path=args.workspace,
        initial_round=args.initial_round,
        max_rounds=args.max_rounds,
        template=args.template,
        name=args.name,
    )

    optimizer.optimize()


if __name__ == "__main__":
    main()

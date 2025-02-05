import argparse
from metagpt.ext.spo.scripts.optimizer import Optimizer
from metagpt.ext.spo.scripts.utils.llm_client import SPO_LLM


def parse_args():
    parser = argparse.ArgumentParser(description='SPO Optimizer CLI')

    # LLM parameter
    parser.add_argument('--optimize-model', type=str, default='claude-3-5-sonnet-20240620',
                        help='Model for optimization')
    parser.add_argument('--optimize-temperature', type=float, default=0.7,
                        help='Temperature for optimization')
    parser.add_argument('--evaluate-model', type=str, default='gpt-4o-mini',
                        help='Model for evaluation')
    parser.add_argument('--evaluate-temperature', type=float, default=0.3,
                        help='Temperature for evaluation')
    parser.add_argument('--execute-model', type=str, default='gpt-4o-mini',
                        help='Model for execution')
    parser.add_argument('--execute-temperature', type=float, default=0,
                        help='Temperature for execution')

    # Optimizer parameter
    parser.add_argument('--workspace', type=str, default='workspace',
                        help='Path for optimized output')
    parser.add_argument('--initial-round', type=int, default=1,
                        help='Initial round number')
    parser.add_argument('--max-rounds', type=int, default=10,
                        help='Maximum number of rounds')
    parser.add_argument('--template', type=str, default='Poem.yaml',
                        help='Template file name')
    parser.add_argument('--name', type=str, default='Poem',
                        help='Project name')
    parser.add_argument('--no-iteration', action='store_false', dest='iteration',
                        help='Disable iteration mode')

    return parser.parse_args()


def main():
    args = parse_args()

    SPO_LLM.initialize(
        optimize_kwargs={
            "model": args.optimize_model,
            "temperature": args.optimize_temperature
        },
        evaluate_kwargs={
            "model": args.evaluate_model,
            "temperature": args.evaluate_temperature
        },
        execute_kwargs={
            "model": args.execute_model,
            "temperature": args.execute_temperature
        }
    )

    optimizer = Optimizer(
        optimized_path=args.workspace,
        initial_round=args.initial_round,
        max_rounds=args.max_rounds,
        template=args.template,
        name=args.name,
        iteration=args.iteration,
    )

    optimizer.optimize()


if __name__ == "__main__":
    main()

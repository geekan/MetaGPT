import argparse
import asyncio

from metagpt.ext.sela.data.custom_task import get_mle_is_lower_better, get_mle_task_id
from metagpt.ext.sela.experimenter.autogluon import GluonExperimenter
from metagpt.ext.sela.experimenter.autosklearn import AutoSklearnExperimenter
from metagpt.ext.sela.experimenter.custom import CustomExperimenter
from metagpt.ext.sela.experimenter.experimenter import Experimenter
from metagpt.ext.sela.experimenter.mcts import MCTSExperimenter
from metagpt.ext.sela.experimenter.random_search import RandomSearchExperimenter


def get_args(cmd=True):
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="")
    parser.add_argument(
        "--exp_mode",
        type=str,
        default="mcts",
        choices=["mcts", "rs", "base", "custom", "greedy", "autogluon", "random", "autosklearn"],
    )
    parser.add_argument("--role_timeout", type=int, default=1000)
    get_di_args(parser)
    get_mcts_args(parser)
    get_rs_exp_args(parser)
    if cmd:
        args = parser.parse_args()
    else:
        args = parser.parse_args("")

    if args.custom_dataset_dir:
        args.external_eval = False
        args.eval_func = "mlebench"
        args.from_scratch = True
        args.task = get_mle_task_id(args.custom_dataset_dir)
        args.low_is_better = get_mle_is_lower_better(args.task)
    return args


def get_mcts_args(parser):
    parser.add_argument("--load_tree", dest="load_tree", action="store_true")
    parser.add_argument("--no_load_tree", dest="load_tree", action="store_false")
    parser.set_defaults(load_tree=False)
    parser.add_argument("--rollouts", type=int, default=5)
    parser.add_argument("--use_fixed_insights", dest="use_fixed_insights", action="store_true")
    parser.set_defaults(use_fixed_insights=False)
    parser.add_argument("--start_task_id", type=int, default=2)
    parser.add_argument(
        "--from_scratch", dest="from_scratch", action="store_true", help="Generate solutions from scratch"
    )
    parser.set_defaults(from_scratch=False)
    parser.add_argument("--no_external_eval", dest="external_eval", action="store_false")
    parser.set_defaults(external_eval=True)
    parser.add_argument("--eval_func", type=str, default="sela", choices=["sela", "mlebench"])
    parser.add_argument("--custom_dataset_dir", type=str, default=None)
    parser.add_argument("--max_depth", type=int, default=4)


def get_rs_exp_args(parser):
    parser.add_argument("--rs_mode", type=str, default="single", choices=["single", "set"])
    parser.add_argument("--is_multimodal", action="store_true", help="Specify if the model is multi-modal")


def get_di_args(parser):
    parser.add_argument("--task", type=str, default="titanic")
    parser.add_argument("--low_is_better", dest="low_is_better", action="store_true")
    parser.set_defaults(low_is_better=False)
    parser.add_argument("--reflection", dest="reflection", action="store_true")
    parser.add_argument("--no_reflection", dest="reflection", action="store_false")
    parser.add_argument("--num_experiments", type=int, default=1)
    parser.add_argument("--special_instruction", type=str, default=None, choices=["ag", "stacking", "text", "image"])
    parser.set_defaults(reflection=True)


async def main(args):
    if args.exp_mode == "mcts":
        experimenter = MCTSExperimenter(args)
    elif args.exp_mode == "greedy":
        experimenter = MCTSExperimenter(args, tree_mode="greedy")
    elif args.exp_mode == "random":
        experimenter = MCTSExperimenter(args, tree_mode="random")
    elif args.exp_mode == "rs":
        experimenter = RandomSearchExperimenter(args)
    elif args.exp_mode == "base":
        experimenter = Experimenter(args)
    elif args.exp_mode == "autogluon":
        experimenter = GluonExperimenter(args)
    elif args.exp_mode == "custom":
        experimenter = CustomExperimenter(args)
    elif args.exp_mode == "autosklearn":
        experimenter = AutoSklearnExperimenter(args)
    else:
        raise ValueError(f"Invalid exp_mode: {args.exp_mode}")
    await experimenter.run_experiment()


if __name__ == "__main__":
    args = get_args()
    asyncio.run(main(args))

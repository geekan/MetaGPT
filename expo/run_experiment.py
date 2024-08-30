from expo.experimenter import MCTSExperimenter, Experimenter, AugExperimenter
import asyncio
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="")
    parser.add_argument("--exp_mode", type=str, default="mcts", choices=["mcts", "aug", "base"])
    get_di_args(parser)
    get_mcts_args(parser)
    get_aug_exp_args(parser)
    return parser.parse_args()


def get_mcts_args(parser):
    parser.add_argument("--load_tree", dest="load_tree", action="store_true")
    parser.add_argument("--no_load_tree", dest="load_tree", action="store_false")
    parser.set_defaults(load_tree=False)
    parser.add_argument("--rollouts", type=int, default=3)

def get_aug_exp_args(parser):
    parser.add_argument("--aug_mode", type=str, default="single", choices=["single", "set"])
    parser.add_argument("--num_experiments", type=int, default=1)


def get_di_args(parser):
    parser.add_argument("--task", type=str, default="titanic")
    parser.add_argument("--low_is_better", dest="low_is_better", action="store_true")
    parser.set_defaults(low_is_better=False)
    parser.add_argument("--reflection", dest="reflection", action="store_true")
    parser.add_argument("--no_reflection", dest="reflection", action="store_false")
    parser.set_defaults(reflection=True)
    

async def main(args):
    if args.exp_mode == "mcts":
        experimenter = MCTSExperimenter(args)
    elif args.exp_mode == "aug":
        experimenter = AugExperimenter(args)
    elif args.exp_mode == "base":
        experimenter = Experimenter(args)
    else:
        raise ValueError(f"Invalid exp_mode: {args.exp_mode}")
    await experimenter.run_experiment()

if __name__ == "__main__":
    args = get_args()
    asyncio.run(main(args))
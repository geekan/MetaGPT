import fire

from metagpt.roles.mi.interpreter import Interpreter


async def main(auto_run: bool = True):
    requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."
    mi = Interpreter(auto_run=auto_run)
    await mi.run(requirement)


if __name__ == "__main__":
    fire.Fire(main)

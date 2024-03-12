import fire

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(auto_run: bool = True):
    requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."
    di = DataInterpreter(auto_run=auto_run)
    await di.run(requirement)


if __name__ == "__main__":
    fire.Fire(main)

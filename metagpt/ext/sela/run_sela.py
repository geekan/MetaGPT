import fire
from runner.sela import SELA

requirement = """
Implement MCTS with a rollout count of 10 to improve my dataset. Focus on forecasting the RS column. 
Carry out data analysis, data preprocessing, feature engineering, and modeling for the forecast. 
Report the rmse on the evaluation dataset, omitting any visual or graphical outputs.
"""


async def main():
    """
    The main function serves as an entry point and supports direct running.
    """
    # Example requirement and data path
    data_dir = "Path/to/dataset"

    # Initialize Sela and run
    sela = SELA()
    await sela.run(requirement, data_dir)


if __name__ == "__main__":
    fire.Fire(main)

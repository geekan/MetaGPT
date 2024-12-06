import fire
from runner.sela import SELA

requirement = (
    "Optimize dataset using MCTS with 10 rollouts. "
    "This is a 05_house-prices-advanced-regression-techniques dataset."
    "Your goal is to predict the target column `SalePrice`."
    "Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target."
    "Report rmse on the eval data. Do not plot or make any visualizations."
)

data_dir = "/Path/to/SELA-datasets/05_house-prices-advanced-regression-techniques"


async def main():
    # Initialize Sela and run
    sela = SELA()
    await sela.run(requirement, data_dir)


if __name__ == "__main__":
    fire.Fire(main)

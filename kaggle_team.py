#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import fire

from metagpt.roles.kaggle_manager import KaggleManager
from metagpt.roles.ml_engineer import MLEngineer
from metagpt.team import Team

async def main(
    # competition: str,
    # data_desc: str,
    # requirement: str,
    investment: float = 5.0,
    n_round: int = 10,
    auto_run: bool = False,
):
    competition, data_desc, requirement = (
        "titanic",
        "Training set is train.csv.\nTest set is test.csv. We also include gender_submission.csv, a set of predictions that assume all and only female passengers survive, as an example of what a submission file should look like.",
        "Run EDA on the train dataset, train a model to predict survival (20% as validation) and save it, predict the test set using saved model, save the test result according to format",
        # "generate a random prediction, replace the Survived column of gender_submission.csv, and save the prediction to a new submission file",
    )

    team = Team()
    team.hire(
        [
            KaggleManager(competition=competition, data_desc=data_desc),
            MLEngineer(goal=requirement, auto_run=auto_run),
        ]
    )

    team.invest(investment)
    team.start_project(requirement)
    await team.run(n_round=n_round)

if __name__ == '__main__':
    fire.Fire(main)

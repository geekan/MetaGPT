from typing import Dict, List, Union, Tuple
import json
import subprocess
import os

import fire
import pandas as pd

from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.roles import Role
from metagpt.actions import Action, BossRequirement
from metagpt.actions.ml_da_action import AskReview, SummarizeAnalysis
from metagpt.schema import Message, Task, Plan
from metagpt.logs import logger
from metagpt.utils.common import CodeParser


os.environ["KAGGLE_USERNAME"] = CONFIG.kaggle_username
os.environ["KAGGLE_KEY"] = CONFIG.kaggle_key

def run_command(cmd):
    print(cmd)
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if output.returncode != 0:
        print("Error output:", output.stderr)
        exit()
    else:
        print(output.stdout)
    return output.stdout

class DownloadData(Action):

    async def run(self, competition, data_desc="") -> str:
        data_path = WORKSPACE_ROOT / competition
        
        output = run_command(f"kaggle competitions list --search {competition}")
        assert output != "No competitions found", "You must provide the correct competition name"
        
        run_command(f"kaggle competitions download {competition} --path {WORKSPACE_ROOT}")
        
        if not os.path.exists(data_path):
        # if True:
            # run_command(f"rm -r {data_path / '*'}")
            run_command(f"unzip -o {WORKSPACE_ROOT / '*.zip'} -d {data_path}")  # FIXME: not safe
        
        file_list = run_command(f"ls {data_path}")

        rsp = f"""
        Location:
        Data downloaded at {data_path} folder, including {file_list}
        Data Description:
        {data_desc}
        """
        return rsp

class SubmitResult(Action):
    PROMPT_TEMPLATE = """
    # Summary
    __summary__
    # Your task
    Extract the file path for test set prediction from the summary above, output a json following the format:
    ```json
    {"file_path": str = "the file path, for example, /path/to/the/prediction/file/xxx.csv, /path/to/the/prediction/file/xxx.xlsx"}
    ```
    """

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    async def _parse_submit_file_path(self, context) -> str:
        prompt = self.PROMPT_TEMPLATE.replace("__summary__", context)
        rsp = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        file_path = json.loads(rsp)["file_path"]
        return file_path

    async def run(self, competition, submit_message="") -> str:
        submit_file_path = await self._parse_submit_file_path(submit_message)

        data_path = WORKSPACE_ROOT / competition
        submit_message = submit_message.replace("'", "")

        run_command(f"kaggle competitions submit {competition} -f {submit_file_path} -m '{submit_message}'")
        run_command(f"kaggle competitions leaderboard --show --csv {competition} > {data_path / 'leaderboard.csv'}")
        run_command(f"kaggle competitions submissions --csv {competition} > {data_path / 'submission.csv'}")
        
        leaderboard = pd.read_csv(data_path / 'leaderboard.csv')
        submission = pd.read_csv(data_path / 'submission.csv')
        print(submission)  # submission.to_json(orient="records")

        submission_score = submission.loc[0, "publicScore"]
        best_score = max(submission["publicScore"])  # might be min
        rank = leaderboard.loc[leaderboard["score"] == best_score].index[0]
        rank_pct = round(rank / len(leaderboard), 4) * 100

        submission_summary = f"""
        # All histories:
        {submission.head(5).to_string()}
        # Current
        Current submission score: {submission_score}, best score: {best_score}, best rank: {rank} (top {rank_pct}%)
        """
        logger.info(submission_summary)
        return submission_summary


class KaggleManager(Role):
    def __init__(
        self, name="ABC", profile="KaggleManager", goal="", competition="titanic", data_desc=""
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._init_actions([DownloadData, SubmitResult])
        self._watch([BossRequirement, SummarizeAnalysis])
        self.competition = competition
        self.data_desc = data_desc  # currently passed in, later can be scrapped down from web by another Role

    async def _think(self):
        observed = self.get_memories()[-1].cause_by
        if observed == BossRequirement:
            self._set_state(0)  # DownloadData, get competition of interest from human, download datasets
        elif observed == SummarizeAnalysis:
            self._set_state(1)  # SubmitResult, get prediction from MLEngineer and submit it to Kaggle

    async def _act(self):
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        if isinstance(todo, DownloadData):
            rsp = await todo.run(self.competition, self.data_desc)

        elif isinstance(todo, SubmitResult):
            submit_message = self.get_memories()[-1].content  # use analysis summary from MLEngineer as submission message
            rsp = await todo.run(competition=self.competition, submit_message=submit_message)

        msg = Message(content=rsp, role="user", cause_by=type(todo))

        return msg

if __name__ == "__main__":
    competition, data_desc, requirement = (
        "titanic",
        "Training set is train.csv.\nTest set is test.csv. We also include gender_submission.csv, a set of predictions that assume all and only female passengers survive, as an example of what a submission file should look like.",
        "Run EDA on the train dataset, train a model to predict survival (20% as validation) and save it, predict the test set using saved model, save the test result according to format",
    )

    summary = "I used Python with pandas for data preprocessing, sklearn's RandomForestClassifier for modeling, and achieved 82.12% accuracy on validation. Predictions saved at '/Users/gary/Desktop/data_agents_opt/workspace/titanic/gender_submission.csv'."

    async def main(requirement: str = requirement):
        role = KaggleManager(competition=competition, data_desc=data_desc)
        # await role.run(Message(content="", cause_by=BossRequirement))
        await role.run(Message(content=summary, cause_by=SummarizeAnalysis))

    fire.Fire(main)
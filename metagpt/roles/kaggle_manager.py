from typing import Dict, List, Union, Tuple
import json
import subprocess

import fire
import pandas as pd

from metagpt.const import WORKSPACE_ROOT
from metagpt.roles import Role
from metagpt.actions import Action, BossRequirement
from metagpt.actions.write_analysis_code import AskReview, SummarizeAnalysis
from metagpt.schema import Message, Task, Plan
from metagpt.logs import logger

import os
os.environ["KAGGLE_USERNAME"] = "xxx"
os.environ["KAGGLE_KEY"] = "xxx"

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
        
        # if not os.path.exists(data_path):
        if True:
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
    # Context
    {context}
    # Your task
    Extract the prediction file for test set, return only the path string, e.g., xxx.csv, xxx.xlsx
    """

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    async def _parse_submit_file_path(self, context) -> str:
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        return rsp

    async def run(self, competition, submit_message="") -> str:
        submit_file_path = self._parse_submit_file_path(submit_message)

        data_path = WORKSPACE_ROOT / competition

        run_command(f"kaggle competitions submit {competition} -f {submit_file_path} -m '{submit_message}'")
        run_command(f"kaggle competitions leaderboard --show --csv {competition} > {data_path / 'leaderboard.csv'}")
        run_command(f"kaggle competitions submissions --csv {competition} > {data_path / 'submission.csv'}")
        
        leaderboard = pd.read_csv(data_path / 'leaderboard.csv')
        submission = pd.read_csv(data_path / 'submission.csv')
        submission_score = submission.loc[0, "publicScore"]
        submission_rank = leaderboard.loc[leaderboard["score"] == submission_score].index[0]
        submission_rank_pct = round(submission_rank / len(leaderboard), 4) * 100

        # best_score = max(submission["publicScore"])
        # best_rank = leaderboard.loc[leaderboard["score"] == best_score].index[0]

        submission_summary = f"""
        ## All History
        {submission.to_json(orient="records")}
        ## Current
        Current submission score: {submission_score}, rank: {submission_rank} (top {submission_rank_pct}%);
        """
        print(submission_summary)
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
        elif observed == SubmitResult:
            self._set_state(2)  # AskReview, ask human for improvement

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

"""
Filename: MetaGPT/examples/werewolf_game/evals/eval.py
Created Date: Oct 18, 2023
Updated Date: Oct 24, 2023
Author: [Aria](https://github.com/ariafyy)
Info: eval the Voting Accuracy Rate of non_werewolves and Vote Difficulity 
"""

import glob
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm
from utils import Utils

from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.environment.werewolf.const import RoleType


class Vote:
    """Vote Evaluation"""

    def __init__(self):
        self.OUT_PATH = DEFAULT_WORKSPACE_ROOT / "outputs"
        os.makedirs(self.OUT_PATH, exist_ok=True)
        self.SUB_FOLDER_LIST = ["01-10", "11-20", "21-30"]

    def _get_log_fileslist(self, IN_PATH) -> list[str]:
        files_list = []
        for SUB_FOLDER in self.SUB_FOLDER_LIST:
            files_list.extend(glob.glob(str(IN_PATH / SUB_FOLDER / "*.txt")))
        return files_list

    def extract_votes_from_logs(self, files_list: list):
        for in_logfile in tqdm(files_list):
            SUB_FOLDER = (Path(in_logfile).parent).stem
            out_txtfile = self.OUT_PATH / "# {0}_{1}.txt".format(SUB_FOLDER, Path(in_logfile).stem)
            Utils().pick_vote_log(in_logfile, out_txtfile)
        votefiles_list = Utils().get_file_list(self.OUT_PATH)
        return votefiles_list

    @staticmethod
    def parse_vote_text2chunks(text: str):
        """
        parse each game vote log into text chunks

        one chunk example:
        ['Player1', 'Player2', 'Player3', 'Player5', 'Player6']. Say ONLY: I vote to eliminate ...
        Player1(Witch): 49 | I vote to eliminate Player5
        Player2(Villager): 49 | I vote to eliminate Player5
        Player3(Villager): 49 | I vote to eliminate Player5
        Player5(Werewolf): 49 | I vote to eliminate Player6
        Player6(Seer): 49 | I vote to eliminate Player5
        """
        pattern = re.compile(r"""\[([^\]]+)\]. Say ONLY: I vote to eliminate ...""")
        chunks = {}
        chunk_id = 0
        last_end = 0
        for match in pattern.finditer(text):
            start = match.start()
            chunk = text[last_end:start]
            chunks[f"vote_{chunk_id}"] = chunk.strip()
            last_end = match.end()
            chunk_id += 1
        final_chunk = text[last_end:].strip()
        if final_chunk:
            chunks[f"vote_{chunk_id}"] = final_chunk
        return chunks

    def _vote_rate_players(self, text: str):
        """
        # calculate the rate of goodteam vote werewolves
        :example:

        input:
        ['Player1', 'Player2', 'Player3', 'Player5', 'Player6']. Say ONLY: I vote to eliminate ...
        Player1(Witch): 49 | I vote to eliminate Player5
        Player2(Villager): 49 | I vote to eliminate Player5
        Player3(Villager): 49 | I vote to eliminate Player5
        Player5(Werewolf): 49 | I vote to eliminate Player6
        Player6(Seer): 49 | I vote to eliminate Player5

        output:
        werewolves:  ['Player5']
        non_werewolves: ['Player1', 'Player2', 'Player3', 'Player6']
        as you can see :Player2(Villager) and   Player3(Villager) vote to eliminate Player5(Werewolf)
        :return goodteam vote rateability: 100.00%
        """
        pattern = re.compile(r"(\w+)\(([^\)]+)\): \d+ \| I vote to eliminate (\w+)")
        # find all werewolves
        werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) == RoleType.WEREWOLF.value:
                werewolves.append(match.group(1))

        # find all non_werewolves
        non_werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) != RoleType.WEREWOLF.value:
                non_werewolves.append(match.group(1))
        num_non_werewolves = len(non_werewolves)

        # count players other than werewolves made the correct votes
        correct_votes = 0
        for match in pattern.finditer(text):
            if match.group(2) != RoleType.WEREWOLF.value and match.group(3) in werewolves:
                correct_votes += 1

        # cal the rateability of non_werewolves
        rate = correct_votes / num_non_werewolves
        good_vote_rate = round(rate, 2)
        return {"good_vote_rate": good_vote_rate, "werewolves": werewolves, "non_werewolves": non_werewolves}

    def get_goodteam_vote_rate(self, text: str) -> float:
        goodteam_vote_rate = self._vote_rate_players(text)["good_vote_rate"]
        return goodteam_vote_rate

    def get_werewolves(self, text: str) -> list:
        werewolves_list = self._vote_rate_players(text)["werewolves"]
        return werewolves_list

    def get_non_werewolves(self, text: str) -> list:
        non_werewolves_list = self._vote_rate_players(text)["non_werewolves"]
        return non_werewolves_list

    def get_votewolf_difficulty(self, werewolves: list, non_werewolves: list) -> str:
        num_living_wolfs = len(werewolves)
        num_living_players = len(werewolves) + len(non_werewolves)
        votewolf_difficulty = "_{0} / {1}".format(num_living_wolfs, num_living_players)
        return votewolf_difficulty

    def get_result_df(self, out_txtfile: str) -> pd.DataFrame:
        """
        folder:  sub folders for evals
        file: evaluation file, each file represents one game
        votes: the number of votes, eg. vote_1 represents the first vote of this game,
        good_vote_rate:the rateability of a good person voting against a werewolf,
                   correct_votes / the total number of players other than werewolves
        total_votes:the total number of votes cast
        """
        with open(out_txtfile, "r") as out_file:
            text = out_file.read()
            chunks = self.parse_vote_text2chunks(text)
            res = []
            for k, v in chunks.items():
                if v != "":
                    chunks_list = list(chunks.keys())
                    total_votes = len(chunks_list) - 1
                    werewolves = self.get_werewolves(v)
                    non_werewolves = self.get_non_werewolves(v)
                    good_vote_rate = self.get_goodteam_vote_rate(v)
                    votewolf_difficulty = self.get_votewolf_difficulty(werewolves, non_werewolves)
                    folder = Utils().filename_to_foldername(out_txtfile)
                    result = {
                        "folder": folder,
                        "file": Path(out_txtfile).stem + ".txt",
                        "vote_round": k,
                        "good_vote_rate": good_vote_rate,
                        "total_votes": total_votes,
                        "votewolf_difficulty": votewolf_difficulty,
                    }
                    res.append(result)
        df = pd.DataFrame(res)
        return df

    def calc_avg_rate(self, IN_PATH) -> pd.DataFrame:
        """
        get avg_rate for each game
        avg_rate : the good_rate/total number of votes in the game
        vote1_rate: First Round Voting Accuracy Rate
        """
        infiles_list = self._get_log_fileslist(IN_PATH)
        votefiles_list = self.extract_votes_from_logs(infiles_list)
        df_list = [self._load_df_from_file(file) for file in votefiles_list]
        combined_df = pd.concat(df_list, ignore_index=True)
        # calculate the average good_vote_rate for each file
        mean_rates = self._calculate_mean_rates(combined_df)
        combined_df["avg_rate"] = combined_df["file"].map(mean_rates)
        # calculate vote1 rate
        vote1_rates = self._calc_vote1_rates(combined_df)
        combined_df["vote1_rate"] = combined_df["folder"].map(vote1_rates.set_index("folder")["good_vote_rate"])
        combined_df.loc[combined_df["vote_round"] != "vote_1", "vote1_rate"] = np.nan
        combined_df["vote1_rate"] = combined_df["vote1_rate"].apply(self._format_rates)
        combined_df["good_vote_rate"] = combined_df["good_vote_rate"].apply(self._format_rates)
        combined_df["avg_rate"] = combined_df["avg_rate"].apply(self._format_rates)
        combined_df.sort_values(["file"], ascending=True, inplace=True)
        return combined_df

    def _calc_vote1_rates(self, df):
        df_vote1 = df[df["vote_round"] == "vote_1"]
        vote1_rates = df_vote1.groupby("folder")["good_vote_rate"].mean().reset_index()
        return vote1_rates

    def _load_df_from_file(self, file):
        return self.get_result_df(file)

    def _calculate_mean_rates(self, df):
        return df.groupby("file")["good_vote_rate"].mean()

    def _format_rates(self, s):
        return Utils().float_to_percent(s)

    def get_eval_csv(self, IN_PATH, EVAL_RESULT):
        """
        IN_PATH : parent folder of ["01-10", "11-20", "21-30"]
        EVAL_RESULT : output csv file path
        """
        combined_df = self.calc_avg_rate(IN_PATH)
        combined_df.to_csv(EVAL_RESULT, index=False)


if __name__ == "__main__":
    IN_PATH = METAGPT_ROOT / "examples/werewolf_game/evals"
    EVAL_RESULT = DEFAULT_WORKSPACE_ROOT / "outputs" / "goodteam_vote_rate.csv"
    Vote().get_eval_csv(IN_PATH, EVAL_RESULT)

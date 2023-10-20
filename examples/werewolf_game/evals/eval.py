'''
Filename: MetaGPT/examples/werewolf_game/evals/eval.py
Created Date: Oct 18, 2023
Revised Date: Oct 20, 2023
Author: [Aria](https://github.com/ariafyy)
Info: eval the vote correct probability of non_werewolves
'''

from metagpt.const import WORKSPACE_ROOT, PROJECT_ROOT
from pathlib import Path
import pandas as pd
import numpy as np
import re
import os, glob
from tqdm import tqdm
from utils import Utils



class Eval:
    """Vote Evaluation"""
    def __init__(self):
        self.OUT_PATH = WORKSPACE_ROOT / "outputs"
        os.makedirs(self.OUT_PATH, exist_ok=True)
        self.SUB_FOLDER_LIST = ["01-10", "11-20", "21-30"]

    def _get_log_fileslist(self, IN_PATH) -> list[str]:
        files_list = []
        for SUB_FOLDER in self.SUB_FOLDER_LIST:
            files_list.extend(glob.glob(str(IN_PATH / SUB_FOLDER / '*.txt')))
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
            chunks[f'vote_{chunk_id}'] = chunk.strip()
            last_end = match.end()
            chunk_id += 1
        final_chunk = text[last_end:].strip()
        if final_chunk:
            chunks[f'vote_{chunk_id}'] = final_chunk
        return chunks


    def get_vote_probability(self, text: str) -> float:
        """
        # calculate the probability of goodteam vote werewolves
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
        :return goodteam vote Probability: 100.00%
        """
        pattern = re.compile(r'(\w+)\(([^\)]+)\): \d+ \| I vote to eliminate (\w+)')
        # find all werewolves
        werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) == 'Werewolf':
                werewolves.append(match.group(1))

        # find all non_werewolves
        non_werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) != 'Werewolf':
                non_werewolves.append(match.group(1))
        num_non_werewolves = len(non_werewolves)

        # count players other than werewolves made the correct votes
        correct_votes = 0
        for match in pattern.finditer(text):
            if match.group(2) != 'Werewolf' and match.group(3) in werewolves:
                correct_votes += 1

        # cal the probability of non_werewolves
        prob = correct_votes / num_non_werewolves
        good_probability = round(prob, 2)
        return good_probability

    def get_result_df(self, out_txtfile: str) -> pd.DataFrame:
        """
        folder:  sub folders for evals
        file: evaluation file, each file represents one game
        votes: the number of votes, eg. vote_1 represents the first vote of this game,
        good_prob:the probability of a good person voting against a werewolf, 
                   correct_votes / the total number of players other than werewolves
        vote_count:the total number of votes cast
        """
        with open(out_txtfile, "r") as out_file:
            text = out_file.read()
            chunks = Eval().parse_vote_text2chunks(text)
            res = []
            for k, v in chunks.items():
                if v != "":
                    chunks_list = list(chunks.keys())
                    vote_count = len(chunks_list) - 1
                    good_probability = Eval().get_vote_probability(v)
                    folder = Utils().filename_to_foldername(out_txtfile)
                    result = {
                        "folder": folder,
                        "file": Path(out_txtfile).stem + ".txt",
                        "votes": k,
                        "good_prob": good_probability,
                        "vote_count": vote_count
                    }
                    res.append(result)
        df = pd.DataFrame(res)
        return df

    def calc_avg_prob(self, IN_PATH) -> pd.DataFrame:
        """
        get avg_prob for each game
        avg_prob : the good_prob/total number of votes in the game
        """
        infiles_list = self._get_log_fileslist(IN_PATH)
        votefiles_list = self.extract_votes_from_logs(infiles_list)
        df_list = [self._load_df_from_file(file) for file in votefiles_list]
        combined_df = pd.concat(df_list, ignore_index=True)
        # calculate the average good_prob for each file
        mean_probs = self._calculate_mean_probs(combined_df)
        combined_df['avg_prob'] = combined_df['file'].map(mean_probs)
        # calculate vote1 prob
        vote1_probs = self._calc_vote1_probs(combined_df)
        combined_df['vote1_prob'] = combined_df['folder'].map(vote1_probs.set_index('folder')['good_prob'])
        combined_df.loc[combined_df['votes'] != 'vote_1', 'vote1_prob'] = np.nan
        combined_df['vote1_prob'] = combined_df['vote1_prob'].apply(self._format_probs)
        combined_df['good_prob'] = combined_df['good_prob'].apply(self._format_probs)
        combined_df['avg_prob'] = combined_df['avg_prob'].apply(self._format_probs)
        combined_df.sort_values(['folder'], ascending=True, inplace=True)
        return combined_df

    def _calc_vote1_probs(self, df):
        df_vote1 = df[df['votes'] == 'vote_1']
        vote1_probs = df_vote1.groupby('folder')['good_prob'].mean().reset_index()
        return vote1_probs

    def _load_df_from_file(self, file):
        return self.get_result_df(file)

    def _calculate_mean_probs(self, df):
        return df.groupby('file')['good_prob'].mean()

    def _format_probs(self, s):
        return Utils().float_to_percent(s)

    def get_eval_csv(self, IN_PATH, EVAL_RESULT):
        """
        IN_PATH : parent folder of ["01-10", "11-20", "21-30"]
        EVAL_RESULT : output csv file path
        """
        combined_df = self.calc_avg_prob(IN_PATH)
        combined_df.to_csv(EVAL_RESULT, index=False)


if __name__ == '__main__':
    IN_PATH = PROJECT_ROOT / "examples/werewolf_game/evals"
    EVAL_RESULT = WORKSPACE_ROOT / "outputs" / 'goodteam_vote_probability.csv'
    Eval().get_eval_csv(IN_PATH, EVAL_RESULT)

'''
Filename: MetaGPT/examples/werewolf_game/evals/eval.py
Created Date: Oct 18, 2023
Updated Date: Oct 19, 2023
Author: [Aria](https://github.com/ariafyy)
Info: eval the vote correct probability of non_werewolves
Files Tree:
    evals
    ├── 01-10
    │         ├── ....txt
    ├── 11-20
    │         ├── ....txt
    ├── 21-30
    │         ├── ....txt
    ├── outputs
    │         ├──# 01-10_....txt
'''

from metagpt.const import PROJECT_ROOT
from pathlib import Path
import pandas as pd
import re
import json
import os, glob
from tqdm import tqdm
from utils import Utils



class Eval:
    """Evaluation"""
    def __init__(self):
        self.OUT_PATH = PROJECT_ROOT / "examples/werewolf_game/evals/outputs"
        os.makedirs(self.OUT_PATH, exist_ok=True)
        self.SUB_FOLDER_LIST = ["01-10", "11-20", "21-30"]

    def get_all_vote_fileslist(self):
        files_list = []
        for SUB_FOLDER in self.SUB_FOLDER_LIST:
            ROOT_PATH = PROJECT_ROOT / ("examples/werewolf_game/evals/{}/").format(SUB_FOLDER)
            tmp_files_list = Utils().get_file_list(ROOT_PATH)
            files_list.extend(tmp_files_list)
        return files_list

    def inlogfile_to_votelog(self, files_list):
        for i in tqdm(range(0, len(files_list))):
            in_logfile = files_list[i]
            SUB_FOLDER = (Path(in_logfile).parent).stem
            out_txtfile = self.OUT_PATH / "# {0}_{1}.txt".format(SUB_FOLDER, Path(in_logfile).stem)
            Utils().pick_vote_log(in_logfile, out_txtfile)

    def get_picked_vote_texts(self):
        files_list = self.get_all_vote_fileslist()
        self.inlogfile_to_votelog(files_list)

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
                    chunksList = list(chunks.keys())
                    vote_count = len(chunksList) - 1
                    good_probability = Eval().get_vote_probability(v)
                    folder = Utils().filename_to_folder(out_txtfile)
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

    def get_avg_prob_df(self):
        """
        get avg_prob for each game
        avg_prob : the good_prob/total number of votes in the game
        """
        out_txtfile_list = Utils().get_file_list(self.OUT_PATH)
        df_list = []
        for i in tqdm(range(0, len(out_txtfile_list))):
            out_txtfile = out_txtfile_list[i]
            file_df = Eval().get_result_df(out_txtfile)
            df_list.append(file_df)
        combined_df = pd.concat(df_list, ignore_index=True)

        # calculate the average good_prob for each file
        mean_probs = combined_df.groupby('file')['good_prob'].mean()
        combined_df['avg_prob'] = combined_df['file'].map(mean_probs)
        combined_df['avg_prob'] = combined_df['avg_prob'].round(2)
        combined_df['good_prob'] = combined_df['good_prob'].apply(lambda x: Utils()._float_to_percent(x))
        combined_df['avg_prob'] = combined_df['avg_prob'].apply(lambda x: Utils()._float_to_percent(x))
        return combined_df

    def get_result_csv(self):
        Eval().get_picked_vote_texts()
        combined_df = self.get_avg_prob_df()
        combined_df.to_csv(self.OUT_PATH / 'goodteam_vote_probability.csv', index=False)


if __name__ == '__main__':
    Eval().get_result_csv()

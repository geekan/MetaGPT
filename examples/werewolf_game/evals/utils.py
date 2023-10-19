'''
Filename: MetaGPT/examples/werewolf_game/evals/utils.py
Created Date: Oct 11, 2023
Author: [Aria](https://github.com/ariafyy)
'''
from metagpt.const import WORKSPACE_ROOT, PROJECT_ROOT
import re
import os,glob

class Utils:
    """Utils: utils of logs"""
    
    @staticmethod
    def polish_log(in_logfile, out_txtfile):
        """polish logs for evaluation"""
        pattern_text = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+) +\| ([\w\.]+:\w+:\d+) - (.*\S)"
        pattern_player = r"(Player(\d{1}): \w+)"
        pattern_start = False
        json_start = False

        with open(in_logfile, "r") as f, open(out_txtfile, "w") as out:
            for line in f.readlines():
                matches = re.match(pattern_text, line)
                if matches:
                    message = matches.group(4).strip()
                    pattern_start = True
                    json_start = False

                    if "Moderator(Moderator) ready to InstructSpeak" not in message and "Moderator(Moderator) ready to ParseSpeak" not in message and "Total running cost:" not in message:
                        out.write("- " + message + '\n')
                    else:
                        out.write('\n')

                elif pattern_start and not matches:
                    if "gpt-4 may update over time" in line:
                        line = ""
                    out.write(line)

                elif line.strip().startswith("{"):
                    out.write(line.strip())
                    json_start = True

                elif json_start and not line.strip().endswith("}"):
                    out.write(line.strip())

                elif json_start and line.strip().endswith("}"):
                    out.write(line.strip())
                    json_start = False

                elif line.startswith("(User):") or line.startswith("********** STEP:") or re.search(pattern_player,line):
                    out.write(line)

                else:
                    out.write("\n")

    @staticmethod
    def pick_vote_log(in_logfile, out_txtfile):
        """
        pick the vote log from the log file.
        ready to AnnounceGameResult serves as the 'key text' which indicates the end of the game.
        """
        pattern_vote = r'(Player\d+)\(([A-Za-z]+)\): (\d+) \| (I vote to eliminate Player\d+)'
        key_text = r"ready to AnnounceGameResult"
        pattern_moderator = r'\[([^\]]+)\]\. Say ONLY: I vote to eliminate ...'
        with open(in_logfile, "r") as f, open(out_txtfile, "w") as out:
            lines = f.readlines()
            start_idx = -1
            # find the index of key_text
            for idx, line in enumerate(lines):
                if key_text in line:
                    start_idx = idx
                    break

            # if find the 'key_text'
            if start_idx >= 0:
                # start from 'key_text' to the end
                relevant_lines = lines[start_idx:]
                for line in relevant_lines:
                    if re.search(pattern_vote, line):
                        out.write(line)
                    if re.search(pattern_moderator, line):
                        out.write(line.lstrip())

    @staticmethod
    def get_file_list(path: str) -> list:
        file_pattern = os.path.join(path, '*.txt')
        files_list = glob.glob(file_pattern)
        return files_list

    @staticmethod
    def _filename_to_folder(out_txtfile: str):
        """convert filename into its parent folder name"""
        s = Path(out_txtfile).stem
        pattern_folder = r'(.+)_'
        match = re.match(pattern_folder, s)
        if match:
            folder = match.group(1)
            return folder

    @staticmethod
    def _float_to_percent(decimal: float) -> str:
        """
        input:  1.00
        output: 100.00%
        """
        percent = decimal * 100
        return f"{percent:.2f}%"

if __name__ == '__main__':
    in_logfile = PROJECT_ROOT / "logs/log.txt"
    out_txtfile = "input your wish path"
    Utils().polish_log(in_logfile, out_txtfile)

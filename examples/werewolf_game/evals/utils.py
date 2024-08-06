"""
Filename: MetaGPT/examples/werewolf_game/evals/utils.py
Created Date: Oct 11, 2023
Revised Date: Oct 20, 2023
Author: [Aria](https://github.com/ariafyy)
"""
import glob
import os
import re
from pathlib import Path

from metagpt.const import METAGPT_ROOT


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

                    if (
                        "Moderator(Moderator) ready to InstructSpeak" not in message
                        and "Moderator(Moderator) ready to ParseSpeak" not in message
                        and "Total running cost:" not in message
                    ):
                        out.write("- " + message + "\n")
                    else:
                        out.write("\n")

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

                elif (
                    line.startswith("(User):") or line.startswith("********** STEP:") or re.search(pattern_player, line)
                ):
                    out.write(line)

                else:
                    out.write("\n")

    @staticmethod
    def pick_vote_log(in_logfile, out_txtfile):
        """
        pick the vote log from the log file.
        ready to AnnounceGameResult serves as the 'HINT_TEXT ' which indicates the end of the game.
        based on bservation and reflection, then discuss is not in vote session.
        """
        pattern_vote = r"(Player\d+)\(([A-Za-z]+)\): (\d+) \| (I vote to eliminate Player\d+)"
        ignore_text = """reflection"""
        HINT_TEXT = r"ready to AnnounceGameResult"
        pattern_moderator = r"\[([^\]]+)\]\. Say ONLY: I vote to eliminate ..."
        in_valid_block = False

        with open(in_logfile, "r") as f:
            lines = f.read()
            split_lines = lines.split(HINT_TEXT)

            if len(split_lines) < 2:
                print(f"Key text :{HINT_TEXT} not found in {in_logfile}")
                return

            relevant_lines = split_lines[1].split("\n")
            with open(out_txtfile, "w") as out:
                for line in relevant_lines:
                    if re.search(pattern_moderator, line):
                        in_valid_block = True
                        out.write(line.lstrip() + "\n")

                    elif in_valid_block and re.search(pattern_vote, line):
                        out.write(line + "\n")
                    elif ignore_text in line:
                        in_valid_block = False

    @staticmethod
    def get_file_list(path: str) -> list:
        file_pattern = os.path.join(path, "*.txt")
        files_list = glob.glob(file_pattern)
        return files_list

    @staticmethod
    def filename_to_foldername(out_txtfile: str):
        """
        convert filename into its parent folder name
        input:"....../# 01-10_10132100.txt"
        output:# 01-10
        """
        s = Path(out_txtfile).stem
        pattern_folder = r"([^_]*)_"
        match = re.match(pattern_folder, s)
        if match:
            folder = match.group(1)
            return folder

    @staticmethod
    def float_to_percent(decimal: float) -> str:
        """
        input:  1.00
        output: 100.00%
        """
        percent = decimal * 100
        return f"{percent:.2f}%"


if __name__ == "__main__":
    in_logfile = METAGPT_ROOT / "logs/log.txt"
    out_txtfile = "input your wish path"
    # Utils().polish_log(in_logfile, out_txtfile)
    Utils().pick_vote_log(in_logfile, out_txtfile)

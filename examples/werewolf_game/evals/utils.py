'''
Filename: MetaGPT/examples/werewolf_game/evals/utils.py
Created Date: Oct 11, 2023
Author: [Aria](https://github.com/ariafyy)
'''
from metagpt.const import WORKSPACE_ROOT, PROJECT_ROOT
import re


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


if __name__ == '__main__':
    in_logfile = PROJECT_ROOT / "logs/log.txt"
    out_txtfile = "input your wish path"
    Utils().polish_log(in_logfile, out_txtfile)

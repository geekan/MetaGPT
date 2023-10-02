#!/usr/bin/env python
# -*- coding:utf-8 -*-


"""
__info："utils for eval"
__author:"[Aria](https://github.com/ariafyy)"
__update："convert txt to json"
"""
from metagpt.const import WORKSPACE_ROOT, PROJECT_ROOT
import re, json


class Utils(object):
    def __init__(self):
        pass

    def _action(self, text: str) -> str:
        """
        # get action
        input: I vote to eliminate Player3
        output: vote
        """
        text = text.lower()
        if "vote" in text:
            action = "vote"
            return action
        if "verify" in text:
            action = "verify"
            return action
        if "kill" in text:
            action = "kill"
            return action
        else:
            action = "chat"
            return action

    def _life(self, text: str) -> str:
        """
        # get life
        input: Kill Player6
        output: dead
        """
        text = text.lower()
        if re.search(r'\b(eliminated|killed|kill)\b', text, re.I):
            life = 'dead'
            dead_role = re.findall(r'\[(.*?)\]', text)
            if re.search(r'no one was killed', text, re.I):
                return "alive", []
            else:
                return life, dead_role
        else:
            life = "alive"
            return life, []

    def txt2data(self, file):
        """
        input: .txt file
        output: data for json format
        """
        result = {}
        count = 0
        day = -1
        flag = False

        with open(file, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Moderator(Moderator): 0" in line:
                    flag = True
                if flag:
                    if "It’s dark, everyone close your eyes." in line:
                        day += 1
                        count = 0
                    data = {}
                    parts = line.split("|")
                    data["role"] = parts[0].strip().split(":")[0]
                    data["day"] = day
                    data["turn"] = count
                    if len(parts) > 1:
                        data["text"] = parts[1].strip()
                        data["action"] = self._action(data["text"])
                        data["life"], data["dead_role"] = self._life(data["text"])
                    else:
                        continue
                    key = "day_{}".format(day)
                    if key not in result:
                        result[key] = []
                    result[key].append(data)
                    count += 1
            return result

    def data2json(self, in_file):
        """
        input:.txt 
        output:.json


        output examples:
        {
          "day_0": [
            {
              "role": "Moderator(Moderator)",
              "day": 0,
              "turn": 0,
              "text": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
              "action": "chat",
              "life": "alive",
              "dead_role": []
            },{}]
            ...
            }
        """
        result = self.txt2data(in_file)
        with open(WORKSPACE_ROOT / 'werewolf_transcript.json', "w", encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')


if __name__ == '__main__':
    txt_path = WORKSPACE_ROOT / "werewolf_transcript.txt"
    log_path = PROJECT_ROOT / "logs/log.txt"
    Utils().data2json(txt_path)

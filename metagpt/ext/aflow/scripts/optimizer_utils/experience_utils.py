import json
import os
from collections import defaultdict

from metagpt.logs import logger
from metagpt.utils.common import read_json_file, write_json_file


class ExperienceUtils:
    def __init__(self, root_path: str):
        self.root_path = root_path

    def load_experience(self, path=None, mode: str = "Graph"):
        if mode == "Graph":
            rounds_dir = os.path.join(self.root_path, "workflows")
        else:
            rounds_dir = path

        experience_data = defaultdict(lambda: {"score": None, "success": {}, "failure": {}})

        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith("round_"):
                round_path = os.path.join(rounds_dir, round_dir)
                try:
                    round_number = int(round_dir.split("_")[1])
                    json_file_path = os.path.join(round_path, "experience.json")
                    if os.path.exists(json_file_path):
                        data = read_json_file(json_file_path, encoding="utf-8")
                        father_node = data["father node"]

                        if experience_data[father_node]["score"] is None:
                            experience_data[father_node]["score"] = data["before"]

                        if data["succeed"]:
                            experience_data[father_node]["success"][round_number] = {
                                "modification": data["modification"],
                                "score": data["after"],
                            }
                        else:
                            experience_data[father_node]["failure"][round_number] = {
                                "modification": data["modification"],
                                "score": data["after"],
                            }
                except Exception as e:
                    logger.info(f"Error processing {round_dir}: {str(e)}")

        experience_data = dict(experience_data)

        output_path = os.path.join(rounds_dir, "processed_experience.json")
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump(experience_data, outfile, indent=4, ensure_ascii=False)

        logger.info(f"Processed experience data saved to {output_path}")
        return experience_data

    def format_experience(self, processed_experience, sample_round):
        experience_data = processed_experience.get(sample_round)
        if experience_data:
            experience = f"Original Score: {experience_data['score']}\n"
            experience += "These are some conclusions drawn from experience:\n\n"
            for key, value in experience_data["failure"].items():
                experience += f"-Absolutely prohibit {value['modification']} (Score: {value['score']})\n"
            for key, value in experience_data["success"].items():
                experience += f"-Absolutely prohibit {value['modification']} \n"
            experience += "\n\nNote: Take into account past failures and avoid repeating the same mistakes, as these failures indicate that these approaches are ineffective. You must fundamentally change your way of thinking, rather than simply using more advanced Python syntax like for, if, else, etc., or modifying the prompt."
        else:
            experience = f"No experience data found for round {sample_round}."
        return experience

    def check_modification(self, processed_experience, modification, sample_round):
        experience_data = processed_experience.get(sample_round)
        if experience_data:
            for key, value in experience_data["failure"].items():
                if value["modification"] == modification:
                    return False
            for key, value in experience_data["success"].items():
                if value["modification"] == modification:
                    return False
            return True
        else:
            return True  # 如果 experience_data 为空，也返回 True

    def create_experience_data(self, sample, modification):
        return {
            "father node": sample["round"],
            "modification": modification,
            "before": sample["score"],
            "after": None,
            "succeed": None,
        }

    def update_experience(self, directory, experience, avg_score):
        experience["after"] = avg_score
        experience["succeed"] = bool(avg_score > experience["before"])

        write_json_file(os.path.join(directory, "experience.json"), experience, encoding="utf-8", indent=4)

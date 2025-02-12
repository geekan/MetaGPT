import datetime
import json
from pathlib import Path
from typing import Dict, List, Union

import pandas as pd

from metagpt.logs import logger


class DataUtils:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.top_scores = []

    def load_results(self, path: Path) -> list:
        result_path = self.get_results_file_path(path)
        if result_path.exists():
            try:
                return json.loads(result_path.read_text())
            except json.JSONDecodeError:
                return []
        return []

    def get_best_round(self):
        self._load_scores()

        for entry in self.top_scores:
            if entry["succeed"]:
                return entry

        return None

    def get_results_file_path(self, prompt_path: Path) -> Path:
        return prompt_path / "results.json"

    def create_result_data(self, round: int, answers: list[dict], prompt: str, succeed: bool, tokens: int) -> dict:
        now = datetime.datetime.now()
        return {"round": round, "answers": answers, "prompt": prompt, "succeed": succeed, "tokens": tokens, "time": now}

    def save_results(self, json_file_path: Path, data: Union[List, Dict]):
        json_path = json_file_path
        json_path.write_text(json.dumps(data, default=str, indent=4))

    def _load_scores(self):
        rounds_dir = self.root_path / "prompts"
        result_file = rounds_dir / "results.json"
        self.top_scores = []

        try:
            if not result_file.exists():
                logger.warning(f"Results file not found at {result_file}")
                return self.top_scores

            data = json.loads(result_file.read_text(encoding="utf-8"))
            df = pd.DataFrame(data)

            for index, row in df.iterrows():
                self.top_scores.append(
                    {
                        "round": row["round"],
                        "succeed": row["succeed"],
                        "prompt": row["prompt"],
                        "answers": row["answers"],
                    }
                )

            self.top_scores.sort(key=lambda x: x["round"], reverse=True)

        except FileNotFoundError:
            logger.error(f"Could not find results file: {result_file}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {result_file}")
        except Exception as e:
            logger.error(f"Unexpected error loading scores: {str(e)}")

        return self.top_scores

    def list_to_markdown(self, questions_list: list):
        """
        Convert a list of question-answer dictionaries to a formatted Markdown string.

        Args:
            questions_list (list): List of dictionaries containing 'question' and 'answer' keys

        Returns:
            str: Formatted Markdown string
        """
        markdown_text = "```\n"

        for i, qa_pair in enumerate(questions_list, 1):
            # Add question section
            markdown_text += f"Question {i}\n\n"
            markdown_text += f"{qa_pair['question']}\n\n"

            # Add answer section
            markdown_text += f"Answer {i}\n\n"
            markdown_text += f"{qa_pair['answer']}\n\n"

            # Add separator between QA pairs except for the last one
            if i < len(questions_list):
                markdown_text += "---\n\n"

        markdown_text += "\n```"

        return markdown_text

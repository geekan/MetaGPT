from pathlib import Path

from metagpt.logs import logger


class PromptUtils:
    def __init__(self, root_path: Path):
        self.root_path = root_path

    def create_round_directory(self, prompt_path: Path, round_number: int) -> Path:
        directory = prompt_path / f"round_{round_number}"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def load_prompt(self, round_number: int, prompts_path: Path):
        prompt_file = prompts_path / "prompt.txt"

        try:
            return prompt_file.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            logger.info(f"Error loading prompt for round {round_number}: {e}")
            raise

    def write_answers(self, directory: Path, answers: dict, name: str = "answers.txt"):
        answers_file = directory / name
        with answers_file.open("w", encoding="utf-8") as file:
            for item in answers:
                file.write(f"Question:\n{item['question']}\n")
                file.write(f"Answer:\n{item['answer']}\n")
                file.write("\n")

    def write_prompt(self, directory: Path, prompt: str):
        prompt_file = directory / "prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

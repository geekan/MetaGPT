import os

from metagpt.logs import logger


class PromptUtils:
    def __init__(self, root_path: str):
        self.root_path = root_path

    def create_round_directory(self, prompt_path: str, round_number: int) -> str:
        directory = os.path.join(prompt_path, f"round_{round_number}")
        os.makedirs(directory, exist_ok=True)
        return directory

    def load_prompt(self, round_number: int, prompts_path: str):
        prompt_file_name = f"{prompts_path}/prompt.txt"

        try:
            with open(prompt_file_name, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError as e:
            logger.info(f"Error loading prompt for round {round_number}: {e}")
            raise

    def write_answers(self, directory: str, answers: dict, name: str = "answers.txt"):
        with open(os.path.join(directory, name), "w", encoding="utf-8") as file:
            for item in answers:
                file.write(f"Question:\n{item['question']}\n")
                file.write(f"Answer:\n{item['answer']}\n")
                file.write("\n")

    def write_prompt(self, directory: str, prompt: str):
        with open(os.path.join(directory, "prompt.txt"), "w", encoding="utf-8") as file:
            file.write(prompt)

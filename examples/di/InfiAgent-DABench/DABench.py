import json
from pathlib import Path

from examples.di.requirements_prompt import DABENCH
from metagpt.const import DABENCH_PATH


# This code is referenced from https://github.com/InfiAgent/InfiAgent/blob/main/examples/DA-Agent/eval_closed_form.py
def evaluate_accuracy_by_question(results):
    correct = sum("correctness" in result and all(result["correctness"].values()) for result in results)
    total = len(results)
    return round(correct / total, 4) if total > 0 else 0


def evaluate_accuracy_by_sub_question(results):
    correct = sum(sum(result["correctness"].values()) for result in results if "correctness" in result)
    total = sum(len(result["correctness"]) for result in results if "correctness" in result)
    return round(correct / total, 4) if total > 0 else 0


def evaluate_accuracy_proportional_by_sub_question_adjusted(results):
    total_score = 0
    for result in results:
        if "correctness" in result:
            sub_question_count = len(result["correctness"])
            score_per_sub_question = 1 / sub_question_count if sub_question_count > 0 else 0
            question_score = sum(result["correctness"].values()) * score_per_sub_question
            total_score += question_score
    return round(total_score / len(results), 4) if results else 0


class DABench:
    def __init__(
        self,
        questions_file=Path(DABENCH_PATH) / "da-dev-questions.jsonl",
        answers_file=Path(DABENCH_PATH) / "da-dev-labels.jsonl",
        template="",
    ):
        # Read questions from a JSONL file
        with open(questions_file, "r") as file:
            self.questions = {int(json.loads(line)["id"]): json.loads(line) for line in file}

        # Read answers from a JSONL file
        with open(answers_file, "r") as file:
            self.answers = {int(json.loads(line)["id"]): json.loads(line) for line in file}

        self.template = template if template else DABENCH

    def get_question(self, question_id):
        """Retrieve the question by its id."""
        return self.questions.get(question_id, "Question not found.")

    def get_prompt(self, question_id):
        """Retrieve the question by its id."""
        temp = self.get_question(question_id)
        return self.template.format(
            question=temp["question"],
            constraints=temp["constraints"],
            format=temp["format"],
            file_name=str(DABENCH_PATH) + "/da-dev-tables/" + temp["file_name"],
            level=temp["level"],
        )

    def get_answer(self, answer_id):
        """Retrieve the answer list by its id."""
        return self.answers.get(answer_id, "Answer not found.")

    def eval(self, id, prediction):
        """Evaluate the prediction against the true label."""
        true_label = self.get_answer(id)["common_answers"]
        # Parse the prediction string into a dictionary of metric-value pairs
        pred_dict = {}
        for pred in prediction.split("@"):
            if pred == "":
                continue
            parts = pred.strip().split("[")
            metric = parts[0].strip().replace(",", "")
            value = parts[1].replace(",", "").replace("]", "")
            try:
                value = float(value)
            except:
                value = value
            pred_dict[metric] = value

        # Sort the true labels to match the order of predictions
        sorted_true_label = sorted(true_label, key=lambda x: x[0])

        # Compare each prediction with the corresponding true label
        correct = True
        for metric, true_value in sorted_true_label:
            try:
                true_value = float(true_value)
            except:
                true_value = true_value
            if isinstance(true_value, (int, float)) and (
                metric not in pred_dict or abs(pred_dict[metric] - true_value) > 1e-6
            ):
                correct = False
                break
            if isinstance(true_value, str) and (metric not in pred_dict or str(pred_dict[metric]) != str(true_value)):
                correct = False
                break

        return correct

    def eval_all(self, id_list, predictions):
        """Evaluate all predictions and calculate accuracy rates."""

        def sigle_eval(id, prediction):
            """Evaluate the prediction against the true label for a single question and return a dictionary indicating the correctness of each metric."""
            true_label = self.get_answer(id)["common_answers"]
            pred_dict = {}

            # Parse the prediction string into a dictionary of metric-value pairs
            for pred in prediction.split("@"):
                if pred == "":
                    continue
                parts = pred.strip().split("[")
                metric = parts[0].strip().replace(",", "")
                value = parts[1].replace(",", "").replace("]", "")
                try:
                    value = float(value)
                except:
                    value = value
                pred_dict[metric] = value

            # Initialize the correctness dictionary with False values
            correctness = {metric: False for metric, _ in true_label}

            # Check each metric's prediction against the true label
            for metric, true_value in true_label:
                try:
                    true_value = float(true_value)
                except:
                    true_value = true_value
                if metric in pred_dict:
                    # Consider the prediction correct if it's within a small tolerance
                    if isinstance(true_value, (int, float)) and abs(pred_dict[metric] - true_value) < 1e-6:
                        correctness[metric] = True
                    if isinstance(true_value, str) and str(pred_dict[metric]) == str(true_value):
                        correctness[metric] = True
            return correctness

        results = []
        for id, prediction in zip(id_list, predictions):
            correct = sigle_eval(id, prediction)
            results.append({"id": id, "correctness": correct})

        # Calculate the three accuracy rates
        accuracy_by_question = evaluate_accuracy_by_question(results)
        accuracy_by_sub_question = evaluate_accuracy_by_sub_question(results)
        proportional_accuracy_by_sub_question = evaluate_accuracy_proportional_by_sub_question_adjusted(results)

        return {
            "accuracy_by_question": accuracy_by_question,
            "accuracy_by_sub_question": accuracy_by_sub_question,
            "proportional_accuracy_by_sub_question": proportional_accuracy_by_sub_question,
        }


if __name__ == "__main__":
    DA = DABench()
    # id = [0, 5, 6]
    # prediction = [
    #     "@mean_fare[34.89]",
    #     "@correlation_coefficient[0.21]",
    #     "@mean_fare_child[31.09], @mean_fare_teenager[31.98], @mean_fare_adult[35.17], @mean_fare_elderly[43.47]",
    # ]
    id = 6
    prediction = (
        "@mean_fare_child[31.09], @mean_fare_teenager[31.98], @mean_fare_adult[35.17], @mean_fare_elderly[43.47]"
    )
    print(DA.eval(id, prediction))
    print(DA.get_answer(id))

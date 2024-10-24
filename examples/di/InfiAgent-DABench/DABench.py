import asyncio
import json
import re
from pathlib import Path

import nest_asyncio

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

    def eval(self, id: str, result: str) -> bool:
        """Evaluate the prediction against the true label."""
        # prediction = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])[-1]["result"]
        prediction = result
        true_label = self.get_answer(id)["common_answers"]
        nest_asyncio.apply()
        cleaned_prediction = prediction.replace("{", "").replace("}", "").replace("'", "")
        if cleaned_prediction:  # Ensure it's not empty
            try:
                pred_dict = parse_prediction(cleaned_prediction)
                if compare_predictions(pred_dict, true_label):
                    return (prediction, True)
            except:
                print("format errer, using gpt to refomat")

        # If the cleaned prediction is not valid, try the async reformat
        try:
            prediction = asyncio.run(
                reformat(self.get_question(id)["question"], self.get_question(id)["format"], result)
            )
            try:
                prediction = prediction.split("Answer{{")[1].split("}}")[0].strip()
            except:
                pass
            pred_dict = parse_prediction(prediction)
            if compare_predictions(pred_dict, true_label):
                return (prediction, True)
        except Exception as e:
            print(f"Error during async reformat: {e}")
            # Skip this step if there's an error

        return (prediction, False)

    def eval_all(self, id_list, predictions):
        """Evaluate all predictions and calculate accuracy rates."""

        def sigle_eval(id, prediction):
            """Evaluate the prediction against the true label for a single question and return a dictionary indicating the correctness of each metric."""
            true_label = self.get_answer(id)["common_answers"]
            prediction = prediction.replace("{", "").replace("}", "").replace("'", "")
            pred_dict = parse_prediction(prediction)
            # Initialize the correctness dictionary with False values
            correctness = {metric: False for metric, _ in true_label}
            # Check each metric's prediction against the true label
            for metric, true_value in true_label:
                try:
                    true_value = float(true_value)
                except:
                    true_value = true_value.replace(",", "")
                if metric in pred_dict:
                    # Consider the prediction correct if it's within a small tolerance
                    if (
                        isinstance(true_value, (int, float))
                        and isinstance(pred_dict[metric], (int, float))
                        and abs(pred_dict[metric] - true_value) < 1e-6
                    ):
                        correctness[metric] = True
                    if isinstance(true_value, str) and (
                        metric not in pred_dict or str(pred_dict[metric]).lower() != str(true_value).lower()
                    ):
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


async def ask_and_print(question, system_prompt):
    from metagpt.llm import LLM

    llm = LLM()
    rsp = await llm.aask(question, system_msgs=[system_prompt])
    return rsp


# This code is referenced from https://github.com/InfiAgent/InfiAgent/blob/main/examples/DA-Agent/reformat.py
async def reformat(question, format, response):
    system_prompt = "You are a helpful assistant."
    demons = """\Format{{
        @shapiro_wilk_statistic[test_statistic]
        @shapiro_wilk_p_value[p_value]
        where "test_statistic" is a number between 0 and 1 representing the Shapiro-Wilk test statistic. Rounding off the answer to two decimal places.
        where "p_value" is a number between 0 and 1 representing the p-value from the Shapiro-Wilk test. Rounding off the answer to four decimal places.
        }}
        \Answer{{
        @shapiro_wilk_statistic[0.56]
        @shapiro_wilk_p_value[0.0002]   
        }}

        \Format{{
        @total_votes_outliers_num[outlier_num]
        where "outlier_num" is an integer representing the number of values considered outliers in the 'total_votes' column.
        }}
        \Answer{{
        @total_votes_outliers[10]   
        }}
        """
    reformat_template = """You should strictly follow the output requirements in the Format part. Here're some examples: {demons}. 
    Your answer should contain all the \"@answer_name[answer]\" in the order mentioned, each \"answer\" should be in the range of value as required. You need to keep the original numbers and text, just reformat without making any changes.
    The format requirements of this question is:
    {format}. You need to keep the original numbers and text, just reformat without making any changes. Please give your answer:"""
    # res = """[['monthly_avg_windspeed', "{'month_1': 7.17, 'month_2': 6.53, 'month_3': 5.9, 'month_4': 6.69, 'month_5': 5.43, 'month_6': 5.82, 'month_7': 5.13, 'month_8': 5.72, 'month_9': 5.69, 'month_10': 6.57, 'month_11': 5.79, 'month_12': 5.52}"]]}"""
    messages = [{"role": "user", "content": question}]
    messages.append({"role": "assistant", "content": response})
    messages.append({"role": "user", "content": reformat_template.format(demons=demons, format=format)})
    rsp = await ask_and_print(messages, system_prompt)
    return rsp


def parse_prediction(prediction: str) -> dict:
    """Parse the prediction string into a dictionary of metric-value pairs."""
    pred_dict = {}
    for pred in prediction.split("@"):
        if pred == "":
            continue
        temp = re.split(r"[\[\]]", pred.strip())
        temp = [s.replace(",", "") for s in temp]
        parts = [s for s in temp if s]
        metric = parts[0].strip().replace(",", "")
        value = parts[-1].replace(",", "").replace(":", "")

        try:
            value = float(value)
        except ValueError:
            pass  # Keep value as string if conversion fails

        pred_dict[metric] = value
    return pred_dict


def compare_predictions(pred_dict: dict, true_label: list) -> bool:
    """Compare each prediction with the corresponding true label."""
    sorted_true_label = sorted(true_label, key=lambda x: x[0])

    for metric, true_value in sorted_true_label:
        try:
            true_value = float(true_value)
        except ValueError:
            true_value = true_value.replace(",", "")

        if isinstance(true_value, (int, float)) and (
            metric not in pred_dict or abs(pred_dict[metric] - true_value) > 1e-6
        ):
            return False
        if isinstance(true_value, str) and (
            metric not in pred_dict or str(pred_dict[metric]).lower() != str(true_value).lower()
        ):
            return False

    return True


if __name__ == "__main__":
    DA = DABench()
    # id = [0, 5, 6]
    # prediction = [
    #     "@mean_fare[34.89]",
    #     "@correlation_coefficient[0.21]",
    #     "@mean_fare_child[31.09], @mean_fare_teenager[31.98], @mean_fare_adult[35.17], @mean_fare_elderly[43.47]",
    # ]
    id = 760
    prediction = "@most_missing_station_name[AGE00135039]@most_missing_station_count[0]"
    print(DA.eval(id, prediction))

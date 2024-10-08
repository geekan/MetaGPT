import json
from pathlib import Path
from metagpt.const import DABENCH_PATH
from examples.di.requirements_prompt import DABENCH
class DABench:
    def __init__(self, questions_file=Path(DABENCH_PATH) / 'da-dev-questions.jsonl', answers_file=Path(DABENCH_PATH) / 'da-dev-labels.jsonl', template = ''):
        # Read questions from a JSONL file
        with open(questions_file, 'r') as file:
            self.questions = {int(json.loads(line)['id']): json.loads(line) for line in file}

        # Read answers from a JSONL file
        with open(answers_file, 'r') as file:
            self.answers = {int(json.loads(line)['id']): json.loads(line) for line in file}

        self.template = template if template else DABENCH
    def get_question(self, question_id):
        """Retrieve the question by its id."""
        return self.questions.get(question_id, "Question not found.")

    def get_prompt(self, question_id):
        """Retrieve the question by its id."""
        temp = self.get_question(question_id)
        return self.template.format(question=temp['question'], constraints=temp['constraints'], format=temp['format'], file_name= str(DABENCH_PATH) + '/da-dev-tables/' + temp['file_name'], level=temp['level'],)

    def get_answer(self, answer_id):
        """Retrieve the answer list by its id."""
        return self.answers.get(answer_id, "Answer not found.")

    def eval(self, id, prediction):
        """Evaluate the prediction against the true label."""
        true_label = self.get_answer(id)['common_answers']
        # Parse the prediction string into a dictionary of metric-value pairs
        pred_dict = {}
        for pred in prediction.split(','):
            parts = pred.strip().split('[')
            metric = parts[0].strip().replace('@', '')
            value = float(parts[1].rstrip(']'))
            pred_dict[metric] = value

        # Sort the true labels to match the order of predictions
        sorted_true_label = sorted(true_label, key=lambda x: x[0])

        # Compare each prediction with the corresponding true label
        correct = True
        for metric, true_value in sorted_true_label:
            if metric not in pred_dict or abs(pred_dict[metric] - float(true_value)) > 1e-6:
                correct = False
                break

        return correct

if __name__ == "__main__":
    DA = DABench()
    id = 6
    prediction = "@mean_fare_child[31.09], @mean_fare_teenager[31.98], @mean_fare_adult[35.17], @mean_fare_elderly[43.47]"
    is_correct = DA.eval(id, prediction)
    print(f"Prediction is {'correct' if is_correct else 'incorrect'}.")
import asyncio

from script.evaluator import QuickEvaluate, QuickExecute
from utils.logs import logger
import tiktoken


def count_tokens(sample):
    if sample is None:
        return 0
    else:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(str(sample['answers'])))

class EvaluationUtils:
    def __init__(self, root_path: str):
        self.root_path = root_path

    async def execute_prompt(self, optimizer, prompt_path, data, model, initial=False, k=3):

        optimizer.prompt = optimizer.prompt_utils.load_prompt(optimizer.round, prompt_path)
        evaluator = QuickExecute(prompt=optimizer.prompt, k=k, model=model)

        answers = await evaluator.prompt_execute()

        cur_round = optimizer.round + 1 if not initial else optimizer.round

        new_data = {"round": cur_round, "answers": answers, "prompt": optimizer.prompt}

        return new_data

    async def evaluate_prompt(self, optimizer, sample, new_sample, path, data, model, initial=False):

        evaluator = QuickEvaluate(k=3)
        original_token = count_tokens(sample)
        new_token = count_tokens(new_sample)

        if initial is True:
            succeed = True
        else:
            evaluation_results = []
            for _ in range(4):
                result = await evaluator.prompt_evaluate(sample=sample, new_sample=new_sample, model=model)
                evaluation_results.append(result)

            logger.info(evaluation_results)

            true_count = evaluation_results.count(True)
            false_count = evaluation_results.count(False)
            succeed = true_count > false_count

        new_data = optimizer.data_utils.create_result_data(new_sample['round'], new_sample['answers'],
                                                           new_sample['prompt'], succeed, new_token)

        data.append(new_data)

        result_path = optimizer.data_utils.get_results_file_path(path)

        optimizer.data_utils.save_results(result_path, data)

        answers = new_sample['answers']

        return succeed, answers

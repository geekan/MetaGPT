import asyncio
from pathlib import Path
from typing import Any, List, Optional, Tuple

import tiktoken

from metagpt.ext.spo.components.evaluator import QuickEvaluate, QuickExecute
from metagpt.logs import logger

EVALUATION_REPETITION = 4


def count_tokens(sample: dict):
    if not sample:
        return 0
    else:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(str(sample["answers"])))


class EvaluationUtils:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    async def execute_prompt(self, optimizer: Any, prompt_path: Path) -> dict:
        optimizer.prompt = optimizer.prompt_utils.load_prompt(optimizer.round, prompt_path)
        executor = QuickExecute(prompt=optimizer.prompt)

        answers = await executor.prompt_execute()

        cur_round = optimizer.round

        new_data = {"round": cur_round, "answers": answers, "prompt": optimizer.prompt}

        return new_data

    async def evaluate_prompt(
        self,
        optimizer: Any,
        samples: Optional[dict],
        new_samples: dict,
        path: Path,
        data: List[dict],
        initial: bool = False,
    ) -> Tuple[bool, dict]:
        evaluator = QuickEvaluate()
        new_token = count_tokens(new_samples)

        if initial is True:
            succeed = True
        else:
            evaluation_results = []

            evaluation_results.extend(
                await asyncio.gather(
                    *(
                        evaluator.prompt_evaluate(samples=samples, new_samples=new_samples)
                        for _ in range(EVALUATION_REPETITION)
                    )
                )
            )

            logger.info(f"Evaluation Results {evaluation_results}")

            true_count = evaluation_results.count(True)
            false_count = evaluation_results.count(False)
            succeed = true_count > false_count

        new_data = optimizer.data_utils.create_result_data(
            new_samples["round"], new_samples["answers"], new_samples["prompt"], succeed, new_token
        )

        data.append(new_data)

        result_path = optimizer.data_utils.get_results_file_path(path)

        optimizer.data_utils.save_results(result_path, data)

        answers = new_samples["answers"]

        return succeed, answers

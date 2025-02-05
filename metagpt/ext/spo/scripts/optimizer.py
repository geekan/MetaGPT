# -*- coding: utf-8 -*-
# @Date    : 8/12/2024 22:00 PM
# @Author  : issac
# @Desc    : optimizer for prompt

import asyncio
import time
from optimizer_utils.data_utils import DataUtils
from optimizer_utils.evaluation_utils import EvaluationUtils
from optimizer_utils.prompt_utils import PromptUtils
from prompt.optimize_prompt import PROMPT_OPTIMIZE_PROMPT
from utils import load
from utils.logs import logger
from utils.llm_client import responser, extract_content
from utils.token_manager import get_token_tracker


class Optimizer:
    def __init__(
            self,
            optimized_path: str = None,
            initial_round: int = 1,
            max_rounds: int = 10,
            name: str = "test",
            template: str = "meta.yaml",
            execute_model=None,
            optimize_model=None,
            evaluate_model=None,
            iteration: bool = True,
    ) -> None:

        self.dataset = name
        self.root_path = f"{optimized_path}/{self.dataset}"
        self.top_scores = []
        self.round = initial_round
        self.max_rounds = max_rounds
        self.execute_model = execute_model
        self.optimize_model = optimize_model
        self.evaluate_model = evaluate_model
        self.iteration = iteration
        self.template = template

        self.prompt_utils = PromptUtils(self.root_path)
        self.data_utils = DataUtils(self.root_path)
        self.evaluation_utils = EvaluationUtils(self.root_path)
        self.token_tracker = get_token_tracker()

    def optimize(self):
        if self.iteration is True:

            for opt_round in range(self.max_rounds):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                score = loop.run_until_complete(self._optimize_prompt())
                self.round += 1
                logger.info(f"Score for round {self.round}: {score}")

                time.sleep(5)

        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            score = loop.run_until_complete(self._test_prompt())
            logger.info(f"Score for round {self.round}: {score}")

    async def _optimize_prompt(self):

        prompt_path = f"{self.root_path}/prompts"
        load.set_file_name(self.template)

        data = self.data_utils.load_results(prompt_path)

        if self.round == 1:
            directory = self.prompt_utils.create_round_directory(prompt_path, self.round)
            # Load prompt using prompt_utils

            prompt, _, _, _ = load.load_meta_data()
            self.prompt = prompt
            self.prompt_utils.write_prompt(directory, prompt=self.prompt)
            new_sample = await self.evaluation_utils.execute_prompt(self, directory, data, model=self.execute_model,
                                                                    initial=True)
            _, answers = await self.evaluation_utils.evaluate_prompt(self, None, new_sample, model=self.evaluate_model,
                                                                     path=prompt_path, data=data, initial=True)
            self.prompt_utils.write_answers(directory, answers=answers)


        _, requirements, qa, count = load.load_meta_data(3)

        directory = self.prompt_utils.create_round_directory(prompt_path, self.round + 1)

        top_round = self.data_utils.get_best_round()

        sample = top_round

        logger.info(f"choose {sample['round']}")

        prompt = sample['prompt']

        golden_answer = self.data_utils.list_to_markdown(qa)
        best_answer = self.data_utils.list_to_markdown(sample["answers"])

        optimize_prompt = PROMPT_OPTIMIZE_PROMPT.format(
            prompt=sample["prompt"], answers=best_answer,
            requirements=requirements,
            golden_answers=golden_answer,
            count=count)

        response = await responser(messages=[{"role": "user", "content": optimize_prompt}],
                                   model=self.optimize_model['name'], temperature=self.optimize_model['temperature'])

        modification = extract_content(response.content, "modification")
        prompt = extract_content(response.content, "prompt")
        if prompt:
            self.prompt = prompt
        else:
            self.prompt = ""

        logger.info(directory)

        self.prompt_utils.write_prompt(directory, prompt=self.prompt)

        new_sample = await self.evaluation_utils.execute_prompt(self, directory, data, model=self.execute_model,
                                                                initial=False)

        success, answers = await self.evaluation_utils.evaluate_prompt(self, sample, new_sample,
                                                                       model=self.evaluate_model, path=prompt_path,
                                                                       data=data, initial=False)

        self.prompt_utils.write_answers(directory, answers=answers)

        logger.info(prompt)
        logger.info(success)

        logger.info(f"now is {self.round + 1}")

        self.token_tracker.print_usage_report()
        usage = self.token_tracker.get_total_usage()

        self.data_utils.save_cost(directory, usage)

        return prompt

    async def _test_prompt(self):

        load.set_file_name(self.template)

        prompt_path = f"{self.root_path}/prompts"
        data = self.data_utils.load_results(prompt_path)

        directory = self.prompt_utils.create_round_directory(prompt_path, self.round)
        # Load prompt using prompt_utils

        new_sample = await self.evaluation_utils.execute_prompt(self, directory, data, model=self.execute_model,
                                                                initial=False, k=100)
        self.prompt_utils.write_answers(directory, answers=new_sample["answers"], name="test_answers.txt")

        logger.info(new_sample)

        logger.info(self.round)

        return None

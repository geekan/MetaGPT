# -*- coding: utf-8 -*-
# @Date    : 8/12/2024 22:00 PM
# @Author  : issac
# @Desc    : optimizer for prompt

import asyncio
import time
from metagpt.ext.spo.scripts.utils.data_utils import DataUtils
from metagpt.ext.spo.scripts.utils.evaluation_utils import EvaluationUtils
from metagpt.ext.spo.scripts.utils.prompt_utils import PromptUtils
from metagpt.ext.spo.prompts.optimize_prompt import PROMPT_OPTIMIZE_PROMPT
from metagpt.ext.spo.scripts.utils import load
from metagpt.logs import logger
from metagpt.ext.spo.scripts.utils.llm_client import extract_content, SPO_LLM



class Optimizer:
    def __init__(
            self,
            optimized_path: str = None,
            initial_round: int = 1,
            max_rounds: int = 10,
            name: str = "",
            template: str = "",
            iteration: bool = True,
    ) -> None:

        self.dataset = name
        self.root_path = f"{optimized_path}/{self.dataset}"
        self.top_scores = []
        self.round = initial_round
        self.max_rounds = max_rounds
        self.iteration = iteration
        self.template = template

        self.prompt_utils = PromptUtils(self.root_path)
        self.data_utils = DataUtils(self.root_path)
        self.evaluation_utils = EvaluationUtils(self.root_path)
        self.llm = SPO_LLM.get_instance()

    def optimize(self):
        if self.iteration is True:

            for opt_round in range(self.max_rounds):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                score = loop.run_until_complete(self._optimize_prompt())
                self.round += 1
                logger.info(f"Score for round {self.round}: {score}")

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
            new_sample = await self.evaluation_utils.execute_prompt(self, directory, initial=True)
            _, answers = await self.evaluation_utils.evaluate_prompt(self, None, new_sample, path=prompt_path, data=data, initial=True)
            self.prompt_utils.write_answers(directory, answers=answers)


        _, requirements, qa, count = load.load_meta_data()

        directory = self.prompt_utils.create_round_directory(prompt_path, self.round + 1)

        top_round = self.data_utils.get_best_round()

        sample = top_round

        logger.info(f"choose {sample['round']}")

        golden_answer = self.data_utils.list_to_markdown(qa)
        best_answer = self.data_utils.list_to_markdown(sample["answers"])

        optimize_prompt = PROMPT_OPTIMIZE_PROMPT.format(
            prompt=sample["prompt"], answers=best_answer,
            requirements=requirements,
            golden_answers=golden_answer,
            count=count)

        response = await self.llm.responser(role="optimize", messages=[{"role": "user", "content": optimize_prompt}])

        modification = extract_content(response, "modification")

        logger.info(f"Modification of this round: {modification}")

        prompt = extract_content(response, "prompt")
        if prompt:
            self.prompt = prompt
        else:
            self.prompt = ""

        logger.info(directory)

        self.prompt_utils.write_prompt(directory, prompt=self.prompt)

        new_sample = await self.evaluation_utils.execute_prompt(self, directory, data)

        success, answers = await self.evaluation_utils.evaluate_prompt(self, sample, new_sample,
                                                                       path=prompt_path,
                                                                       data=data, initial=False)

        self.prompt_utils.write_answers(directory, answers=answers)

        logger.info(prompt)
        logger.info(success)

        logger.info(f"now is {self.round + 1}")

        return prompt

    async def _test_prompt(self):

        load.set_file_name(self.template)

        prompt_path = f"{self.root_path}/prompts"
        data = self.data_utils.load_results(prompt_path)

        directory = self.prompt_utils.create_round_directory(prompt_path, self.round)
        # Load prompt using prompt_utils

        new_sample = await self.evaluation_utils.execute_prompt(self, directory, data)
        self.prompt_utils.write_answers(directory, answers=new_sample["answers"], name="test_answers.txt")

        logger.info(new_sample)

        logger.info(self.round)

        return None

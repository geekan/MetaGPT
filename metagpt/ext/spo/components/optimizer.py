# -*- coding: utf-8 -*-
# @Date    : 8/12/2024 22:00 PM
# @Author  : issac
# @Desc    : optimizer for prompt

import asyncio

from metagpt.ext.spo.prompts.optimize_prompt import PROMPT_OPTIMIZE_PROMPT
from metagpt.ext.spo.utils import load
from metagpt.ext.spo.utils.data_utils import DataUtils
from metagpt.ext.spo.utils.evaluation_utils import EvaluationUtils
from metagpt.ext.spo.utils.llm_client import SPO_LLM, RequestType, extract_content
from metagpt.ext.spo.utils.prompt_utils import PromptUtils
from metagpt.logs import logger


class PromptOptimizer:
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
        if self.iteration:
            for opt_round in range(self.max_rounds):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                prompt = loop.run_until_complete(self._optimize_prompt())
                self.round += 1
                # logger.info(f"Prompt generated in round {self.round}: {prompt}")
            self.show_final_result()

        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            prompt = loop.run_until_complete(self._test_prompt())
            # logger.info(f"Prompt generated in round {self.round}: {prompt}")

    def show_final_result(self):

        best_round = self.data_utils.get_best_round()

        logger.info("\n" + "=" * 50)
        logger.info("\n🏆 OPTIMIZATION COMPLETED - FINAL RESULTS 🏆\n")
        logger.info(f"\n📌 Best Performing Round: {best_round['round']}")
        logger.info(f"\n🎯 Final Optimized Prompt:\n{best_round['prompt']}")
        logger.info("\n" + "=" * 50 + "\n")

    async def _optimize_prompt(self):
        prompt_path = f"{self.root_path}/prompts"
        load.set_file_name(self.template)

        data = self.data_utils.load_results(prompt_path)

        if self.round == 1:

            logger.info("\n⚡ RUNNING Round 1 PROMPT ⚡\n")

            directory = self.prompt_utils.create_round_directory(prompt_path, self.round)
            # Load prompt using prompt_utils

            prompt, _, _, _ = load.load_meta_data()
            self.prompt = prompt
            self.prompt_utils.write_prompt(directory, prompt=self.prompt)
            new_samples = await self.evaluation_utils.execute_prompt(self, directory, initial=True)
            _, answers = await self.evaluation_utils.evaluate_prompt(
                self, None, new_samples, path=prompt_path, data=data, initial=True
            )
            self.prompt_utils.write_answers(directory, answers=answers)

        _, requirements, qa, count = load.load_meta_data()

        directory = self.prompt_utils.create_round_directory(prompt_path, self.round + 1)

        samples = self.data_utils.get_best_round()

        logger.info(f"\n🚀Round {self.round+1} OPTIMIZATION STARTING 🚀\n")
        logger.info(f"\nSelecting prompt for round {samples['round']} and advancing to the iteration phase\n")


        golden_answer = self.data_utils.list_to_markdown(qa)
        best_answer = self.data_utils.list_to_markdown(samples["answers"])

        optimize_prompt = PROMPT_OPTIMIZE_PROMPT.format(
            prompt=samples["prompt"],
            answers=best_answer,
            requirements=requirements,
            golden_answers=golden_answer,
            count=count,
        )

        response = await self.llm.responser(
            request_type=RequestType.OPTIMIZE, messages=[{"role": "user", "content": optimize_prompt}]
        )

        modification = extract_content(response, "modification")

        logger.info(f"Modification of {self.round+1} round: {modification}")

        prompt = extract_content(response, "prompt")

        if prompt:
            self.prompt = prompt
        else:
            self.prompt = ""

        logger.info("\n🎯 NEW PROMPT GENERATED 🎯\n")
        logger.info(f"\nRound {self.round+1} Prompt: {self.prompt}\n")

        self.prompt_utils.write_prompt(directory, prompt=self.prompt)

        logger.info("\n⚡ RUNNING OPTIMIZED PROMPT ⚡\n")

        new_samples = await self.evaluation_utils.execute_prompt(self, directory)

        logger.info("\n📊 EVALUATING OPTIMIZED PROMPT 📊\n")

        success, answers = await self.evaluation_utils.evaluate_prompt(
            self, samples, new_samples, path=prompt_path, data=data, initial=False
        )

        self.prompt_utils.write_answers(directory, answers=answers)

        logger.info("\n🎯 OPTIMIZATION RESULT 🎯\n")
        logger.info(f"\nRound {self.round + 1} Optimization: {'✅ SUCCESS' if success else '❌ FAILED'}\n")

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

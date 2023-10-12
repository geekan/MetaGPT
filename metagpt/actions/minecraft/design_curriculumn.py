# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:56
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json
import re

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from metagpt.document_store import FaissStore

from metagpt.logs import logger
from metagpt.actions.minecraft.player_action import PlayerActions as Action
from metagpt.utils.minecraft import load_prompt, fix_and_parse_json
from metagpt.schema import HumanMessage, SystemMessage
from metagpt.const import CKPT_DIR


class DesignTask(Action):
    """
    Action class for decomposing a task.
    Refer to the code in the voyager/agents/curriculum.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def decompose_task(self, query, events):
        system_msgs = SystemMessage(
            content=load_prompt("curriculum_task_decomposition")
        )
        prompt = self.render_human_message(
            events=events, chest_observation=""
        ) + HumanMessage(content=f"Final task: {query}")
        logger.info(f"Curriculum Agent task decomposition\nFinal task: {query}")

        rsp = await self._aask(prompt=prompt, system_msgs=system_msgs)
        logger.info(f"Curriculum Agent task decomposition\n{rsp}")
        return fix_and_parse_json(rsp)

    def parse_llm_response(self, llm_resp):
        task = ""
        for line in llm_resp.split("\n"):
            if line.startswith("Task:"):
                task = line[5:].replace(".", "").strip()
        assert task, "Task not found in Curriculum Agent response"
        return {"next_task": task}

    async def generate_task(self, human_msg, system_msg, max_retries=5):
        """
        Refer to the code in the voyager/agents/curriculum.py propose_next_ai_task() for implementation details.
        Returns: task & context

        """

        if max_retries == 0:
            raise RuntimeError("Max retries reached, failed to propose task.")
        curriculum = await self._aask(prompt=human_msg, system_msgs=system_msg)
        logger.info(f"Curriculum Agent message\n{curriculum}")
        try:
            response = self.parse_llm_response(
                curriculum
            )  # Task: Craft 4 wooden planks.
            logger.info(f"Parsed Curriculum Agent response\n{response}")
            assert "next_task" in response
            return response["next_task"]
        except Exception as e:
            logger.info(f"Error parsing curriculum response: {e}. Trying again!")
            return await self.generate_task(
                human_msg=human_msg,
                system_msg=system_msg,
                max_retries=max_retries - 1,
            )

    async def run(self, human_msg, system_msg, *args, **kwargs):
        logger.info(f"run {self.__repr__()}")

        # Call the language model to generate a response.

        task = await self.generate_task(human_msg=human_msg, system_msg=system_msg)

        return task


class DesignCurriculum(Action):
    """
    Action class for designing curriculum-related questions.
    Refer to the code in the voyager/agents/curriculum.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def generate_qa(self, events, qa_cache, qa_cache_questions_vectordb, game_memory, human_msg, system_msg):
        """
        Generate qa for DesignTask's HumanMessage
        """
        questions_new = await self.generate_qa_step1(
            events=events, human_msg=human_msg, system_msg=system_msg
        )
        logger.debug(f"Generate_qa_step1 result list is HERE: {questions_new}")

        questions = []
        answers = []
        for question in questions_new:
            if qa_cache_questions_vectordb._collection.count() > 0:
                docs_and_scores = (
                    qa_cache_questions_vectordb.similarity_search_with_score(
                        question, k=1
                    )
                )
                if docs_and_scores and docs_and_scores[0][1] < 0.05:
                    question_cached = docs_and_scores[0][0].page_content
                    assert question_cached in qa_cache
                    answer_cached = qa_cache[question_cached]
                    questions.append(question_cached)
                    answers.append(answer_cached)
                    continue
            answer = await self.generate_qa_step2(question=question)
            assert question not in qa_cache
            qa_cache[question] = answer
            qa_cache_questions_vectordb.add_texts(
                texts=[question],
            )
            with open(f"{CKPT_DIR}/curriculum/qa_cache.json", "w") as f:
                json.dump(qa_cache, f)
            qa_cache_questions_vectordb.persist()
            questions.append(question)
            answers.append(answer)

        game_memory.qa_cache = qa_cache
        

        assert len(questions_new) == len(questions) == len(answers)
        logger.info(f"Curriculum Agent generate_qa Questions: {questions}")
        logger.info(f"Curriculum Agent generate_qa Answers: {answers}")
        return questions, answers

    async def generate_qa_step1(self, events, human_msg, system_msg):
        biome = events[-1][1]["status"]["biome"].replace("_", " ")
        questions = [
            f"What are the blocks that I can find in the {biome} in Minecraft?",
            f"What are the items that I can find in the {biome} in Minecraft?",
            f"What are the mobs that I can find in the {biome} in Minecraft?",
        ]
        qa_response = await self._aask(prompt=human_msg, system_msgs=system_msg)

        try:
            # Regex pattern to extract question and concept pairs
            pattern = r"Question \d+: (.+)\nConcept \d+: (.+)"
            # Extracting all question and concept pairs from the text
            pairs = re.findall(pattern, qa_response)
            # Storing each question and concept in separate lists
            questions_new = [pair[0] for pair in pairs]
            questions.extend(questions_new)
        except Exception as e:
            logger.error(
                f"Error parsing curriculum response for "
                f"QA step 1 ask questions: {e}."
            )
        return questions

    async def generate_qa_step2(self, question):
        # Implement the logic for another specific step in generating questions and answers.
        # logger.info(f"Curriculum Agent generate_qa_step2 Question: {question}")
        human_msg = HumanMessage(content=f"Question: {question}").content
        system_msg = [
            SystemMessage(
                content=load_prompt("curriculum_qa_step2_answer_questions")
            ).content
        ]
        answer = await self._aask(prompt=human_msg, system_msgs=system_msg)
        # logger.info(f"Curriculum Agent generate_qa_step2 answer: {answer}")
        return answer

    async def get_context_from_task(self, task, qa_cache, qa_cache_questions_vectordb, game_memory):
        """
        Args: task
        Returns: context: "Question: {question}\n{answer}"
        if include ore in question, gpt will try to use tool with skill touch enhancement to mine
        """

        question = (
            f"How to {task.replace('_', ' ').replace(' ore', '').replace(' ores', '').replace('.', '').strip().lower()}"
            f" in Minecraft?"
        )
        if question in qa_cache:
            answer = qa_cache[question]
        else:
            answer = await self.generate_qa_step2(question=question)
            qa_cache[question] = answer
            qa_cache_questions_vectordb.add_texts(
                texts=[question],
            )
            with open(f"{CKPT_DIR}/curriculum/qa_cache.json", "w") as f:
                json.dump(qa_cache, f)
            qa_cache_questions_vectordb.persist()

        game_memory.qa_cache = qa_cache
        context = f"Question: {question}\n{answer}"
        return context

    async def generate_context(self, task, qa_cache, qa_cache_questions_vectordb, game_memory, max_retries=5):
        """
        Refer to the code in the voyager/agents/curriculum.py propose_next_ai_task() for implementation details.
        Returns: context

        """

        if max_retries == 0:
            raise RuntimeError("Max retries reached, failed to propose context.")
        try:
            context = await self.get_context_from_task(
                task=task, qa_cache=qa_cache, qa_cache_questions_vectordb=qa_cache_questions_vectordb,
                game_memory=game_memory,
            )  # Curriculum Agent Question: How to craft 4 wooden planks in Minecraft? & Curriculum Agent Answer: ...
            return context
        except Exception as e:
            logger.info(f"Error parsing curriculum response: {e}. Trying again!")
            return await self.generate_context(
                task=task,
                qa_cache=qa_cache,
                qa_cache_questions_vectordb=qa_cache_questions_vectordb,
                game_memory=game_memory,
                max_retries=max_retries - 1,
            )

    async def run(self, task, qa_cache, qa_cache_questions_vectordb, game_memory, human_msg, system_msg, *args,
                  **kwargs):
        logger.info(f"run {self.__repr__()}")
        # Generate curriculum-related questions and answers.
        # curriculum_qustion = await self.generate_qa_step1(events, human_msg, system_msg)
        curriculum_context = await self.generate_context(task, qa_cache, qa_cache_questions_vectordb,
                                                         game_memory=game_memory)

        # Return the generated questions and answers.
        return curriculum_context

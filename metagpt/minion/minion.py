#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : brain.py
"""
import re
import uuid
from typing import List

from jinja2 import Template
from pydantic import BaseModel, Field

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.minion.python_env import PythonEnv


class MetaPlanner(BaseModel):
    name: str = Field(default="naive", description="The name of stragety.")
    score: float = Field(
        default=0,
        description="estimate score of choosing this stragety of success, 1.0 means perfect match,"
        "if we choose this stragety, we are most likely to solve this problem, 0.0 means a"
        "bad match, if we choose this stragety, we are most likely fail to solve this problem",
    )
    complexity: str = Field(
        default="",
        description="estimate this problem's difficulty, when the problem is simple,only required one or several steps to solve this problem,"
        "return low, when the problem difficulty is medium and require more steps to solve it, return medium,"
        "when the problem seemed quite difficult, generally should involve complex process and careful step planning to solve it,"
        "return high",
    )
    query_range: str = Field(
        default="",
        description="if it's a short range query that only require few steps, few context memory to complete the query, return short, "
        "otherwise multiple step, require long term range attention to store relevant long context memory,"
        "return long",
    )  # short range query, or multiple step range like writing a very long novel
    num_trials: int = Field(
        default=0,
        description="number of trials to try using the strategy to solve this problem, sometimes one strategy may fail, but we retry this strategy"
        "we'll succeed, so need need some number of trials",
    )
    is_finished: bool = Field(
        default=False, description="Whether current question already been answered by current answer"
    )


class Plan(BaseModel):
    task_id: str = Field(
        default="some id",
        description="unique identifier for a task in plan, can be an ordinal",
    )
    dependent_task_ids: List[str] = Field(
        default_factory=list,
        description="ids of tasks prerequisite to this task",
    )
    instruction: str = Field(
        default="some instruction",
        description="what you should do in this task, one short phrase or sentence",
    )
    task_type: str = Field(
        default="some task type",
        description="type of this task",
    )
    task_params: str = Field(
        default="{}",
        description="a json dictionary of task parameters and values",
    )


ASK_PROMPT = """context:
{input.short_context}
instruction:
{input.instruction}
query_type:
{input.query_type}
query:
{input.query}
"""

ASK_PROMPT2 = """context:
{{input.short_context}}
instruction:
{{input.instruction}}
query_type:
{{input.query_type}}
query:
{{input.query}}
"""

CHOOSE_WORKER_MINION_TEMPLATE = (
    """
List:
{% for key,minion in minions.items() %}
1. **ID:** {{ key }}  
   **Description:** 
   "{{ minion.__doc__ }}"
{% endfor %}

Please return strategy name for the question:
Please note, since the strategy name is used as class name, you must ensure the returned strategy name upper or lower case must match *EXACTLY* the name I provided here.

"""
    + ASK_PROMPT2
)

SMART_PROMPT_TEMPLATE = (
    """You are an advanced language model proficient in answering questions requiring world knowledge but facing challenges with math problems. When you encounter a math problem, you should employ a math strategy or python strategy to ensure a comprehensive and accurate solution.

"""
    + CHOOSE_WORKER_MINION_TEMPLATE
)
PLAN_PROMPT = (
    """You are a strategic planner capable of designing and executing complex plans. When a user presents a task, your first step is to outline how each strategy will be utilized. Then, you implement the strategies to accomplish the task. Below is a list of strategies available to you:

"""
    + ASK_PROMPT2
    + """ 

# Task:
Based on the context, write a plan or modify an existing plan of what you should do to achieve the goal. A plan consists of one to {max_tasks} tasks.
If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes. Give the whole plan unless instructed to modify only one task of the plan.
If you encounter errors on the current task, revise and output the current single task only.

Output a list of jsons following the format:
    ```json
    [
        {
            "task_id": str = "unique identifier for a task in plan, can be an ordinal",
        "dependent_task_ids": list[str] = "ids of tasks prerequisite to this task",
        "instruction": "what you should do in this task, one short phrase or sentence",
        "task_type": "type of this task",
        "task_params": "a json dictionary of task parameters and values"
        },
        ...
    ]

"""
)

PLAN_PROMPT_BY_CHOOSING = (
    """You are a strategic planner capable of designing and executing complex plans. When a user presents a task, your first step is to outline how each strategy will be utilized. Then, you implement the strategies to accomplish the task. Below is a list of strategies available to you:

Web: Begin by accessing the web to gather necessary information. Subsequently, use this information for further inference and decision-making.
Given the following question, identify the most appropriate strategy to employ. Ensure that the returned strategy name matches EXACTLY in upper or lower case as provided.
also for each strategy, please identify necessary params need to pass, like subquestion etc.

"""
    + CHOOSE_WORKER_MINION_TEMPLATE
)
DIVIDE_PROMPT = """
For the following question and existing answer, determine whether the answer already contains answer to the question without need for furthur processing, Otherwise if it needs furthur processing, This is the List of stragety that you can use:
List:

Naive:Native Strategy, Directly ask the LLM for an answer.
CoT:Chain of Thought (CoT) Strategy, Ask the LLM to think step-by-step, explaining each part of the problem to enhance the accuracy of the answer.
ToT:Tree of Thought (ToT) Strategy, Break the problem down into a tree structure, providing different suboptions for each step. Analyze each suboption, prioritizing the most promising paths. If a path leads to a solution, return that result; if not, backtrace and explore other suboptions.
Ee:Explore and Exploit Strategy, Utilize a memory of previous similar questions to choose the best result based on past metrics or explore new approaches to update the memory with better results if they surpass the original metric.
Math: This is a problem involve math, you need to use math tool to solve it
Python: This problem requires writing code to solve it, write python code to solve it

question:
{question}
Here's currently thought plan, Then return a list of strategy name for the question:
Please note, since the strategy name is used as class name, you must ensure the returned strategy name upper or lower case must match *EXACTLY* the name I provided here.
plan:
{plan}
"""

SCORE_PROMPT = """Given a complex question and its corresponding answer, analyze the answer to determine its correctness. Break down the analysis into the following steps:

1. Identify the key elements of the question.
2. Evaluate if the provided answer addresses each key element accurately.
3. Check for logical consistency and the presence of supporting evidence in the answer.
4. Consider alternative perspectives and if the answer sufficiently accounts for them.
5. Synthesize your findings to determine the overall correctness of the answer.
6. Assign a confidence score for the correctness of the answer, with 1.0 being completely correct and 0.0 being completely incorrect. Only output the score value.

"""

FINISH_PROMPT = (
    """
[Input Prompt] for the following question and existing answer, determine whether the answer already contains answer to the question without need for furthur processing, Otherwise if it needs furthur processing, This is the List of stragety that you can use:
"""
    + ASK_PROMPT
)


def extract_content(text):
    pattern = r"\[CONTENT\](.*?)\[/CONTENT\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def snake_case_to_camel_case(snake_str: str, suffix: str = "Minion") -> str:
    # Split the snake case string by underscores and capitalize each word
    components = snake_str.split("_")
    # Capitalize each component and join them
    camel_case_str = "".join(x.capitalize() for x in components)
    # Add the suffix
    camel_case_with_suffix = camel_case_str + suffix
    return camel_case_with_suffix


def camel_case_to_snake_case(camel_str: str, suffix: str = "Minion") -> str:
    # Remove the suffix
    if camel_str.endswith(suffix):
        camel_str = camel_str[: -len(suffix)]

    # Find all places where a lowercase letter is followed by an uppercase letter
    snake_case_str = re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()
    return snake_case_str


class SubclassHookMeta(type):
    def __init__(cls, name, bases, clsdict):
        super().__init__(name, bases, clsdict)
        cls._subclassed_hook()


MINION_REGISTRY = {}


class Minion(metaclass=SubclassHookMeta):
    def __init__(self, input=None, brain=None, id=None, score_func=None):
        if brain is None:
            raise ValueError("The 'brain' parameter cannot be None.")

        self.id = id or uuid.uuid4()

        self.input = input
        self.brain = brain
        self.followers = []
        self.score_func = score_func

    def propagate_information(self, other):
        other.input = self.input
        other.brain = self.brain

    async def score(self):
        # if self.score_func is not None:
        #     return self.score_func(self)
        minion = ScoreMinion(input=self.input, brain=self.brain)
        return await minion.execute()

    @classmethod
    def _subclassed_hook(cls):
        if cls.__name__ != "Minion":
            MINION_REGISTRY[camel_case_to_snake_case(cls.__name__)] = cls
        # print(f"{cls.__name__} has been subclassed")

    def add_followers(self, follower):
        self.followers.append(follower)

    def __hash__(self):
        # Use a tuple of attributes to compute the hash value
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return False

    def __repr__(self):
        return f"Minion({self.id})"

    async def is_finished(self):
        # check whether self is finished
        meta_planner = await ActionNode.from_pydantic(MetaPlanner).fill(
            context=FINISH_PROMPT.format(input=self.input), llm=self.brain.llm
        )

        is_finished = meta_planner.instruct_content.is_finished
        return is_finished

    @property
    def clean_answer(self):
        answer = extract_content(self.answer_node.content)
        return answer

    async def execute(self):
        node = ActionNode(key="answer", expected_type=str, instruction="let's think step by step", example="")
        node = await node.fill(context=ASK_PROMPT.format(input=self.input), llm=self.brain.llm)
        self.answer_node = node
        self.answer = self.input.answer = node.instruct_content.answer
        return self.answer  # maybe also adds score?


class CotMinion(Minion):
    """Chain of Thought (CoT) Strategy, Ask the LLM to think step-by-step, explaining each part of the problem to enhance the accuracy of the answer. Please noted you can't access web or user's local computer, so if you need information from the web or from user's local computer, DON'T USE THIS STRATEGY."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input.instruction = "let's think step by step to solve this problem"


class MultiPlanMinion(Minion):
    "This Strategy will first generate multiple plan, and then compare each plan, see which one is more promising to produce good result, first try most promising plan, then to less promising plan."
    pass


class PlanMinion(Minion):
    "Divide and Conquer Strategy, Divide the problem into smaller subproblems, solve each subproblem independently, and then merge the results for the final solution."

    async def execute(self):
        choose_template = Template(PLAN_PROMPT)

        # filter out smart, since we don't want choose smart following smart again
        # also filter out ScoreMinion
        filtered_registry = {
            key: value
            for key, value in MINION_REGISTRY.items()
            if key != "smart" and key != "score" and key != "plan" and key != "multi_plan"
        }
        filled_template = choose_template.render(minions=filtered_registry, input=self.input)

        plan = await ActionNode.from_pydantic(Plan).fill(context=filled_template, llm=self.brain.llm, schema="raw")

        plan

        # class_name = node.instruct_content.name
        # if class_name in filtered_registry:
        #     klass = filtered_registry[class_name]  # get the Minion
        # else:
        #     # print(f"Class {class_name} not found.")
        #     klass = filtered_registry["cot"]  # default we use CoTMinion
        # num_trials = 1
        # scores = {}
        # for i in range(num_trials):  # generate a list of children
        #     minion = klass(question=node.instruct_content.subquestion)
        #     self.add_followers(minion)
        #     await minion.execute()
        #     score = await minion.score()
        #     scores[minion] = score
        #
        # # if the score is too low, then maybe we add some more iterations?
        # sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        #
        # # Extract keys and values
        # sorted_keys = [item[0] for item in sorted_items]
        # sorted_values = [item[1] for item in sorted_items]
        # for i, minion in enumerate(sorted_keys):
        #     if await minion.is_finished():
        #         self.answer = minion.answer
        #         self._score = sorted_values[i]
        #         return minion.answer  # .content
        #     else:
        #         minion = SmartMinion(question=minion.question + minion.answer)
        #         self._score = minion.score
        #         await minion.execute()
        #         # should we also determine score, is_finished etc? I don't think so since we're using SmartMinion
        #         return minion.answer


class PythonMinion(Minion):
    "This problem requires writing code to solve it, write python code to solve it"

    # """This problem is a simple math problem, can write code to solve it.
    # Then directly use python stragety to solve it, return python, don't return math.
    # Or this problem requires writing code to solve it, write python code to solve it
    # """

    async def execute(self):
        error = ""
        for i in range(5):
            node = ActionNode(
                key="code",
                expected_type=str,
                instruction="Write python code to solve the problem, also noted the python program must return a string print out answer that describe how the problem is solved,"
                "please remember I may have not python pip installed, so please add in the code like"
                """import os
                            os.system('python -m pip install sympy')
                            """,
                example="",
            )
            node = await node.fill(
                context=(
                    ASK_PROMPT
                    + """

also please check previous error, do the modification according to previous error if there's previous error.
Previous error:
{error}
                """
                ).format(input=self.input, error=error),
                llm=LLM(),
            )
            code = node.instruct_content.code
            self.answer_node = code

            image_name = "intercode-python"
            env = PythonEnv(image_name, verbose=True)
            # env = PythonEnv("metagpt/metagpt:latest", verbose=True)
            result = env.step(code)
            obs = result[0]  # obs

            if obs["error"]:
                error = obs["error"]
                continue  # try again?
            output, error = obs["output"], obs["error"]
            self.answer = output
            return self.answer  # obs


# class WebMinion(PythonMinion):
#     "This task require access web to get information, write python code to get the information"
#     def __init__(self, question, id=None):
#         super().__init__(question, id)
#         self.question = (
#             "This task require access web to get information, write python code to get the information, question:"
#             + self.question
#         )


class MathMinion(PythonMinion):
    "This is a problem involve math, you need to use math tool to solve it"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input.instruction = "This is a math problem, write python code to solve it"


class ScoreMinion(Minion):
    async def execute(self):
        # if self.input.score_func, handles that
        node = ActionNode(key="score", expected_type=float, instruction=SCORE_PROMPT, example="")
        node = await node.fill(
            context=ASK_PROMPT
            + """
                answer:
                {input.answer}
                """.format(
                input=self.input
            ),
            llm=self.brain.llm,
        )
        return node.instruct_content.score


class SmartMinion(Minion):
    async def execute(self):
        choose_template = Template(SMART_PROMPT_TEMPLATE)

        # filter out smart, since we don't want choose smart following smart again
        # also filter out ScoreMinion
        filtered_registry = {key: value for key, value in MINION_REGISTRY.items() if key != "smart" and key != "score"}
        filled_template = choose_template.render(minions=filtered_registry, input=self.input)

        meta_planner = await ActionNode.from_pydantic(MetaPlanner).fill(context=filled_template, llm=self.brain.llm)
        num_trials = meta_planner.instruct_content.num_trials
        if num_trials < 1 or not isinstance(num_trials, int):
            num_trials = 1

        name = meta_planner.instruct_content.name
        if name in filtered_registry:
            klass = filtered_registry[name]  # get the Minion
        else:
            # print(f"Class {class_name} not found.")
            klass = filtered_registry["cot"]  # default we use CoTMinion

        scores = {}
        for i in range(num_trials):  # generate a list of children
            minion = klass(input=self.input, brain=self.brain)
            self.add_followers(minion)
            await minion.execute()
            score = await minion.score()
            scores[minion] = score

        # if the score is too low, then maybe we add some more iterations?
        sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        # Extract keys and values
        sorted_keys = [item[0] for item in sorted_items]
        sorted_values = [item[1] for item in sorted_items]
        for i, minion in enumerate(sorted_keys):
            # if await minion.is_finished():
            self.answer = self.input.answer = minion.answer
            self._score = sorted_values[i]
            return minion.answer, self._score

            # else:
            #     minion = SmartMinion(input=self.input, brain=self.brain)
            #     self._score = minion.score
            #     await minion.execute()
            #     # should we also determine score, is_finished etc? I don't think so since we're using SmartMinion
            #     return minion.answer, self._score

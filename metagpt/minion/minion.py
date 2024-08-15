#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : brain.py
"""
import json
import os
import re
import uuid
from typing import List

import networkx as nx
from jinja2 import Template
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_none

from metagpt.actions.action_node import ActionNode
from metagpt.const import METAGPT_ROOT
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.minion.python_env import PythonEnv
from metagpt.minion.save_plan import save_json_to_file
from metagpt.minion.task_graph import convert_tasks_to_graph


def extract_json_from_string(text):
    # Regular expression pattern to match content between ```json and ```
    pattern = r"```json\s*([\s\S]*?)\s*```"

    # Search for the pattern in the input text
    match = re.search(pattern, text)

    if match:
        json_content = match.group(1)  # Extract the JSON content
        try:
            # Convert the JSON string to a Python object
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON content.") from e
    else:
        raise ValueError("No JSON content found.")


def extract_final_answer(text):
    match = re.search(r"<final_answer>\s*(.*?)\s*</final_answer>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


class MetaPlan(BaseModel):
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


COT_PROBLEM_INSTRUCTION = """
Let's approach this problem by breaking it down into distinct, logical steps. For each step, provide a clear explanation of the reasoning behind it. Consider any underlying assumptions, explore potential alternative approaches, and evaluate the consequences of each decision. Once you have thoroughly analyzed all aspects, synthesize the findings to reach a well-supported conclusion. Finally, present your answer clearly within the tags <final_answer></final_answer>.
"""
ASK_PROMPT = """context:
{input.short_context}
instruction:
{input.instruction}
query_type:
{input.query_type}
query:
{input.query}
"""

ASK_PROMPT_JINJA = """context:
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
    + ASK_PROMPT_JINJA
)

SMART_PROMPT_TEMPLATE = (
    """You are an advanced language model proficient in answering questions requiring world knowledge but facing challenges with math problems. When you encounter a math problem, you should employ a math strategy or python strategy to ensure a comprehensive and accurate solution.

"""
    + CHOOSE_WORKER_MINION_TEMPLATE
)
TASK_INPUT = """
Current Task Input:
instruction:
{{task.instruction}}
task type:
{{task.task_type}}
task parameters:
{% for key,minion in task.task_params.items() %}
1. **Name:** {{ key }}  
   **Value:** 
   "{{ minion }}"
{% endfor %}
hint:
{{task.hint}}
"""
TASK_PROMPT = (
    """Given the task's context, instructions, parameters, and provided hints, analyze the situation and evaluate multiple worker strategies. Identify potential outcomes for each strategy and select the most effective approach. Justify your choice by considering both immediate and long-term implications, as well as any trade-offs or risks associated with your decision. Additionally, explore how alternative strategies might alter the task's outcome and what contingencies could be prepared to address unforeseen challenges.
"""
    + CHOOSE_WORKER_MINION_TEMPLATE
    + ASK_PROMPT_JINJA
    + TASK_INPUT
)
PLAN_PROMPT = (
    """You are a strategic planner capable of designing and executing complex plans. When a user presents a task, your first step is to outline how each strategy will be utilized. Then, you implement the strategies to accomplish the task. Below is a list of strategies available to you:

"""
    + ASK_PROMPT_JINJA
    + """ 

Task:

Given the context, create a detailed plan or refine an existing plan to achieve a specified goal. A comprehensive plan should consist of one to {max_tasks} tasks. The following points outline the necessary steps:

    Detailed Task Construction: Each task in the plan must be described clearly and should include specific actions, conditions, and parameters that guide its execution. Avoid generic steps; instead, ensure that each task is actionable and contributes directly to the overall objective.

    Critical Evaluation of Dependencies: When refining or modifying an existing plan, critically analyze dependencies between tasks. If revising a single task, assess how it interacts with previous or subsequent tasks and ensure that it aligns with the overall flow of the plan. Modify only what is necessary, maintaining the integrity of the original structure unless fundamental changes are needed for optimization.

    Error Handling and Adaptation: In case of errors or obstacles in executing a task, revise the specific task to address the issue effectively. The revision should include precise instructions on how to overcome the challenge, minimizing disruption to the plan's progress.

    JSON Output Specifications: Provide the final plan as a list of JSON objects, ensuring each task includes the following attributes:
        task_id: A unique identifier for each task, preferably ordinal or descriptive.
        dependent_task_ids: A list of task IDs that are prerequisites for this task, indicating dependencies.
        instruction: A concise but clear description of the action required for this task.
        task_type: The type or category of the task.
        task_params: A JSON dictionary specifying the task's parameters and their corresponding values.
        Hint: (Optional) Provide a hint or brief guidance for carrying out the task effectively, particularly if the task involves complexity or potential challenges. This could include tips, best practices, or a brief outline of steps to ensure successful completion.

    Contextual Precision: Return a plan that is as specific and precise as possible. Avoid vague or ambiguous instructions. Ensure that task descriptions and parameters are well-defined to facilitate smooth execution and alignment with the overall goal.

By following these guidelines, ensure the plan is logical, thorough, and well-suited to achieving the desired outcome efficiently.
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


# a dummy score that does nothing, always return 1 to shortcut the score process
class NoneScore:
    def __call__(self, **kwargs):
        return 1


class SubclassHookMeta(type):
    def __init__(cls, name, bases, clsdict):
        super().__init__(name, bases, clsdict)
        cls._subclassed_hook()


MINION_REGISTRY = {}


class Minion(metaclass=SubclassHookMeta):
    def __init__(self, input=None, brain=None, id=None, score_func=None, task=None):
        if brain is None:
            raise ValueError("The 'brain' parameter cannot be None.")

        self.id = id or uuid.uuid4()

        self.input = input
        self.brain = brain
        self.followers = []
        self.score_func = score_func
        self.task = task

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
        meta_planner = await ActionNode.from_pydantic(MetaPlan).fill(
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

    async def execute(self):
        node = ActionNode(key="answer", expected_type=str, instruction="let's think step by step", example="")
        node = await node.fill(
            context=(COT_PROBLEM_INSTRUCTION + ASK_PROMPT).format(input=self.input), llm=self.brain.llm, schema="raw"
        )
        self.answer_node = node
        self.answer = self.input.answer = extract_final_answer(node.content)
        self.answer_raw = self.input.answer_raw = node.content
        return self.answer  # maybe also adds score?


class MultiPlanMinion(Minion):
    "This Strategy will first generate multiple plan, and then compare each plan, see which one is more promising to produce good result, first try most promising plan, then to less promising plan."
    pass


class PlanMinion(Minion):
    "Divide and Conquer Strategy, Divide the problem into smaller subproblems, solve each subproblem independently, and then merge the results for the final solution."

    @retry(stop=stop_after_attempt(3), wait=wait_none())  # Retries up to 3 times with a 2-second wait between attempts
    async def get_plan_with_retry(self, cache_filename=None):
        if cache_filename:
            cache_filename = (
                "/Users/femtozheng/python-project/MetaGPT/logs/plan/json_plan_f2a8a06b-dffa-44bd-a0e8-3005e4e37c57.json"
            )

            # Attempt to load the plan from the cache
            import json

            try:
                if os.path.exists(cache_filename):
                    with open(cache_filename, "r") as file:
                        plan = json.load(file)
                        logger.info("Plan loaded from cache.")
                        return plan
                else:
                    logger.info("Cache file not found. Fetching plan with retry.")
            except (IOError, json.JSONDecodeError) as e:
                logger.info(f"Error loading plan from cache: {e}. Fetching plan with retry.")
        choose_template = Template(PLAN_PROMPT)

        # filter out smart, since we don't want to choose smart following smart again
        # also filter out ScoreMinion
        filtered_registry = {
            key: value
            for key, value in MINION_REGISTRY.items()
            if key != "smart" and key != "score" and key != "plan" and key != "multi_plan"
        }
        filled_template = choose_template.render(minions=filtered_registry, input=self.input)

        plan = await ActionNode.from_pydantic(Plan).fill(context=filled_template, llm=self.brain.llm, schema="raw")

        json = extract_json_from_string(plan.content)
        return json

    async def execute(self):
        log_dir = METAGPT_ROOT / "logs" / "plan"

        # Create the directory, including any necessary parent directories
        log_dir.mkdir(parents=True, exist_ok=True)
        filename = log_dir / f"json_plan_{self.id}.json"
        self.plan = await self.get_plan_with_retry(cache_filename=filename)

        save_json_to_file(self.plan, filename)

        self.task_graph = convert_tasks_to_graph(self.plan)
        # plot_graph(self.task_graph)
        await self.execute_tasks_in_order(self.task_graph)
        self.answer = self.input.answer = "task completed"

    async def execute_tasks_in_order(self, graph):
        # Perform topological sorting
        sorted_tasks = list(nx.topological_sort(graph))

        for task_id in sorted_tasks:
            # Execute the task (replace this with your actual task execution logic)
            for task in self.plan:
                if task["task_id"] == task_id:
                    task_minion = TaskMinion(brain=self.brain, input=self.input, task=task)
                    await task_minion.execute()

            print(f"Executing task {task_id}: {task['label']}")


class TaskMinion(Minion):
    async def choose_minion(self):
        choose_template = Template(TASK_PROMPT)

        # filter out smart, since we don't want choose smart following smart again
        # also filter out ScoreMinion
        filtered_registry = {key: value for key, value in MINION_REGISTRY.items() if key != "smart" and key != "score"}
        filled_template = choose_template.render(minions=filtered_registry, input=self.input, task=self.task)

        # if self.input.route:
        #     return filtered_registry[self.input.route]

        meta_plan = await ActionNode.from_pydantic(MetaPlan).fill(context=filled_template, llm=self.brain.llm)
        self.num_trials = meta_plan.instruct_content.num_trials
        if self.num_trials < 1 or not isinstance(self.num_trials, int):
            self.num_trials = 1

        name = meta_plan.instruct_content.name
        if name in filtered_registry:
            klass = filtered_registry[name]  # get the Minion
        else:
            # print(f"Class {class_name} not found.")
            klass = filtered_registry["cot"]  # default we use CoTMinion
        return klass

    async def execute(self):
        klass = await self.choose_minion()
        klass


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
                instruction="Write python code to solve the problem, also noted the python program must return a string print out answer and only answer,"
                "please remember I may have not python pip installed, so please add in the code like"
                """import os
                            os.system('python -m pip install sympy')
                            """
                "Please ensure all the variables are defined, don't use variables before defining them,"
                "please ensure you correctly indent the code, and don't use // as comment",
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
            self.answer_code = code
            print(self.answer_code)

            image_name = "intercode-python"
            env = PythonEnv(image_name, verbose=False, is_agent=True)
            # env = PythonEnv("metagpt/metagpt:latest", verbose=True)
            result = env.step(code)
            obs = result[0]  # obs

            if obs["error"]:
                error = obs["error"]
                continue  # try again?
            output, error = obs["output"], obs["error"]
            self.answer = self.input.answer = output
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


class CodeProblemMinion(PlanMinion):
    "This is a coding problem which requires stragety thinking to solve it, you will first explore the stragety space then solve it"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input.instruction = "This is a coding problem which requires stragety thinking to solve it, you will first explore the stragety space then solve it"


class ScoreMinion(Minion):
    def __init__(self, **kwargs):
        super(ScoreMinion, self).__init__(**kwargs)
        self.score = None  # clear self.score to avoid loop

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


class RouteMinion(Minion):
    async def choose_minion(self):
        choose_template = Template(SMART_PROMPT_TEMPLATE)

        # filter out smart, since we don't want choose smart following smart again
        # also filter out ScoreMinion
        filtered_registry = {key: value for key, value in MINION_REGISTRY.items() if key != "smart" and key != "score"}
        filled_template = choose_template.render(minions=filtered_registry, input=self.input)

        if self.input.route:
            return filtered_registry[self.input.route]

        meta_plan = await ActionNode.from_pydantic(MetaPlan).fill(context=filled_template, llm=self.brain.llm)
        self.num_trials = meta_plan.instruct_content.num_trials
        if self.num_trials < 1 or not isinstance(self.num_trials, int):
            self.num_trials = 1

        name = meta_plan.instruct_content.name
        if name in filtered_registry:
            klass = filtered_registry[name]  # get the Minion
        else:
            # print(f"Class {class_name} not found.")
            klass = filtered_registry["cot"]  # default we use CoTMinion
        return klass

    async def execute(self):
        klass = await self.choose_minion()

        scores = {}
        for i in range(self.input.num_trials):  # generate a list of children
            minion = klass(input=self.input, brain=self.brain)
            self.add_followers(minion)
            self.answer = self.input.answer = await minion.execute()
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

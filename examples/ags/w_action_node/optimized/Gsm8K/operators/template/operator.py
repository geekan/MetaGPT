# import random
# from collections import Counter
# from typing import Dict, List, Tuple

# from tenacity import retry, stop_after_attempt

# from examples.ags.w_action_node.operator import Operator
# from examples.ags.w_action_node.optimized.Gsm8K.operators.template.op_prompt import *
# from examples.ags.w_action_node.optimized.Gsm8K.operators.template.operator_an import *
# from metagpt.actions.action_node import ActionNode
# from metagpt.llm import LLM


# class Custom(Operator):
#     def __init__(self, llm: LLM, name: str = "Custom"):
#         super.__init__(name, llm)

#     async def __call__(self, input, instruction):
#         prompt = input + instruction
#         node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
#         response = node.instruct_content.model_dump()
#         return response


# class Generate(Operator):
#     def __init__(self, llm: LLM, name: str = "Generate"):
#         super().__init__(name, llm)

#     async def __call__(self, problem):
#         prompt = Generate_PROMPT.format(problem_description=problem)
#         node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
#         response = node.instruct_content.model_dump()
#         return response


# class ContextualGenerate(Operator):
#     def __init__(self, llm: LLM, name: str = "ContextualGenerate"):
#         super().__init__(name, llm)

#     @retry(stop=stop_after_attempt(3))
#     async def __call__(self, problem, context):
#         prompt = ContextualGenerate_PROMPT.format(problem_description=problem, thought=context)
#         # prompt = CONTEXTUAL_GENERATE_PROMPT.format(problem_description=problem, thought=context)
#         node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
#         response = node.instruct_content.model_dump()
#         return response


# class Format(Generate):
#     def __init__(self, name: str = "Format", llm: LLM = LLM()):
#         super().__init__(name, llm)

#     # 使用JSON MODE 输出 Formatted 的结果
#     async def __call__(self, problem, solution):
#         prompt = FORMAT_PROMPT.format(problem_description=problem, solution=solution)
#         node = await ActionNode.from_pydantic(FormatOp).fill(context=prompt, llm=self.llm)
#         response = node.instruct_content.model_dump()
#         return response  # {"solution":"xxx"}


# class Review(Operator):
#     def __init__(self, criteria: str = "accuracy", name: str = "Review", llm: LLM = LLM()):
#         self.criteria = criteria
#         super().__init__(name, llm)

#     async def __call__(self, problem, solution):
#         prompt = REVIEW_PROMPT.format(problem_description=problem, solution=solution, criteria=self.criteria)
#         node = await ActionNode.from_pydantic(ReviewOp).fill(context=prompt, llm=self.llm)
#         response = node.instruct_content.model_dump()
#         return response  # {"review_result": True, "feedback": "xxx"}


# class Revise(Operator):
#     def __init__(self, name: str = "Revise", llm: LLM = LLM()):
#         super().__init__(name, llm)

#     async def __call__(self, problem, solution, feedback):
#         prompt = REVISE_PROMPT.format(problem_description=problem, solution=solution, feedback=feedback)
#         node = await ActionNode.from_pydantic(ReviseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
#         response = node.instruct_content.model_dump()
#         return response  # {"solution": "xxx"}


# class FuEnsemble(Operator):
#     """
#     Function: Critically evaluating multiple solution candidates, synthesizing their strengths, and developing an enhanced, integrated solution.
#     """

#     def __init__(self, name: str = "FuEnsemble", llm: LLM = LLM()):
#         super().__init__(name, llm)

#     async def __call__(self, solutions: List, problem):
#         solution_text = ""
#         for solution in solutions:
#             solution_text += str(solution) + "\n"
#         prompt = FU_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
#         node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm)
#         response = node.instruct_content.model_dump()
#         return {"solution": response["final_solution"]}  # {"final_solution": "xxx"}


# class MdEnsemble(Operator):
#     """
#     Paper: Can Generalist Foundation Models Outcompete Special-Purpose Tuning? Case Study in Medicine
#     Link: https://arxiv.org/abs/2311.16452
#     """

#     def __init__(self, name: str = "MdEnsemble", llm: LLM = LLM(), vote_count: int = 3):
#         super().__init__(name, llm)
#         self.vote_count = vote_count

#     @staticmethod
#     def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
#         shuffled_solutions = solutions.copy()
#         random.shuffle(shuffled_solutions)
#         answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
#         return shuffled_solutions, answer_mapping

#     async def __call__(self, solutions: List[str], problem: str):
#         print(f"solution count: {len(solutions)}")
#         all_responses = []

#         for _ in range(self.vote_count):
#             shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)

#             solution_text = ""
#             for index, solution in enumerate(shuffled_solutions):
#                 solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

#             prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
#             node = await ActionNode.from_pydantic(MdEnsembleOp).fill(context=prompt, llm=self.llm)
#             response = node.instruct_content.model_dump()

#             answer = response.get("solution_letter", "")
#             answer = answer.strip().upper()

#             if answer in answer_mapping:
#                 original_index = answer_mapping[answer]
#                 all_responses.append(original_index)

#         most_frequent_index = Counter(all_responses).most_common(1)[0][0]
#         final_answer = solutions[most_frequent_index]
#         return {"solution": final_answer}  # {"final_solution": "xxx"}


# class Rephrase(Operator):
#     """
#     Paper: Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering
#     Link: https://arxiv.org/abs/2404.14963
#     Paper: Achieving >97% on GSM8K: Deeply Understanding the Problems Makes LLMs Better Solvers for Math Word Problems
#     Link: https://arxiv.org/abs/2404.14963
#     """

#     def __init__(self, name: str = "Rephrase", llm: LLM = LLM()):
#         super().__init__(name, llm)

#     async def __call__(self, problem: str) -> str:
#         prompt = REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem)
#         node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
#         response = node.instruct_content.model_dump()
#         return response  # {"rephrased_problem": "xxx"}

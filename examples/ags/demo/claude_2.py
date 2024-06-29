from metagpt import nn
import metagpt.functional as F

class Generate(nn.Module):
    def __init__(self, model_name):
        super(Generate, self).__init__()
        self.model = nn.LLM(model_name)

    def forward(self, prompt):
        return self.model.generate(prompt)

class Review(nn.Module):
    def __init__(self, criteria):
        super(Review, self).__init__()
        self.criteria = criteria

    def forward(self, generated_code):
        return F.analyze(generated_code, self.criteria)

class Revise(nn.Module):
    def __init__(self, model_name):
        super(Revise, self).__init__()
        self.model = nn.LLM(model_name)

    def forward(self, original_code, review_feedback):
        prompt = f"Original code:\n{original_code}\n\nFeedback:\n{review_feedback}\n\nRevised code:"
        return self.model.generate(prompt)

class Ensemble(nn.Module):
    def __init__(self, strategy='majority_vote'):
        super(Ensemble, self).__init__()
        self.strategy = strategy

    def forward(self, solutions):
        return F.ensemble(solutions, strategy=self.strategy)

class LLMAgent(nn.Module):
    def __init__(self, generate_model, review_criteria, revise_model):
        super(LLMAgent, self).__init__()
        self.generate = Generate(generate_model)
        self.review = Review(review_criteria)
        self.revise = Revise(revise_model)
        self.ensemble = Ensemble()

    def forward(self, problem_description, num_iterations=3):
        solutions = []
        for _ in range(num_iterations):
            # 生成初始解决方案
            initial_solution = self.generate(problem_description)
            
            # 审查解决方案
            review_feedback = self.review(initial_solution)
            
            # 根据反馈修改解决方案
            revised_solution = self.revise(initial_solution, review_feedback)
            
            solutions.append(revised_solution)

        # 整合多个解决方案
        final_solution = self.ensemble(solutions)
        return final_solution

# 示例使用
problem = """
Human: Write a function that takes a list of numbers and returns the sum of the numbers at even indices.

Function Signature:
def sum_even_indices(numbers: List[int]) -> int:

Example:
>>> sum_even_indices([1, 2, 3, 4, 5])
9  # 1 + 3 + 5 = 9
"""

agent = LLMAgent(
    generate_model="gpt-3.5-turbo",
    review_criteria=["correctness", "efficiency", "readability"],
    revise_model="gpt-4"
)

solution = agent(problem)
print(solution)

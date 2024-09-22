from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.humaneval import humaneval_evaluation
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import List

DEBATE_INITIAL_PROMPT = """
{question}\nPlease provide a step-by-step explanation in text, followed by your Python function without any additional text or test cases. 
"""

DEBATE_PROMPT = """
{question}
Considering the solutions provided by other agents as additional suggestions. Please think carefully and provide an updated python function without any additional text or test cases. 
"""

FINAL_DECISION_PROMPT = """
{question}
Considering all the thinking processes and answers:
{all_thinking}
{all_answers}
Please reason carefully and provide the final answer. Make sure the code output is wrapped with ```python``` without any additional text or test cases.
"""

class DebateOp(BaseModel):
    thinking: str = Field(default="", description="think")
    answer: str = Field(default="", description="answer")

class FinalDecisionOp(BaseModel):
    solution: str = Field(default="", description="final answer")

class DebateAgent(Operator):
    def __init__(self, llm: LLM, name: str, role: str):
        super().__init__(name, llm)
        self.role = role

    async def __call__(self, problem: str, function_name: str, context: List[str] = None, mode: str = None):
        role_prompt = f"You are a {self.role}. Based on your professional knowledge and thinking style,"
        if context is None:
            prompt = role_prompt + DEBATE_INITIAL_PROMPT.format(question=problem)
        else:
            prompt = role_prompt + DEBATE_PROMPT.format(question=problem) + "\n".join(context)
        
        fill_kwargs = {"context": prompt, "llm": self.llm, "function_name":function_name}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(DebateOp).fill(**fill_kwargs)
        return node.instruct_content.model_dump()

class FinalDecisionAgent(Operator):
    def __init__(self, llm: LLM, name: str = "FinalDecision"):
        super().__init__(name, llm)

    async def __call__(self, problem: str, function_name, all_thinking: List[str], all_answers: List[str], mode: str = None):
        prompt = FINAL_DECISION_PROMPT.format(
            question=problem,
            all_thinking="\n".join(all_thinking),
            all_answers="\n".join(all_answers)
        )
        fill_kwargs = {"context": prompt, "llm": self.llm, "function_name":function_name}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(FinalDecisionOp).fill(**fill_kwargs)
        return node.instruct_content.model_dump()

class MultiPersonaGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.debate_agents = [
            DebateAgent(self.llm, f"Debate Agent {i}", role)
            for i, role in enumerate([
                'Innovative CS Thinker - ICPC Competitor',
                'Critical Reasoning Expert - Math Professor',
                'Computational Thinking Specialist - Computer Science Researcher'
            ])
        ]
        self.final_decision_agent = FinalDecisionAgent(self.llm)

    async def __call__(self, problem, function_name):
        max_round = 2
        all_thinking = [[] for _ in range(max_round)]
        all_answers = [[] for _ in range(max_round)]

        for r in range(max_round):
            for i, agent in enumerate(self.debate_agents):
                if r == 0:
                    result = await agent(problem, function_name, mode="context_fill")
                else:
                    context = [f"{agent.role}'s previous round thinking: {all_thinking[r-1][i]}"] + \
                              [f"{self.debate_agents[j].role}'s thinking: {all_thinking[r-1][j]}" for j in range(len(self.debate_agents)) if j != i]
                    result = await agent(problem, context, mode="context_fill")
                all_thinking[r].append(result["thinking"])
                all_answers[r].append(result["answer"])

        final_result = await self.final_decision_agent(
            problem,
            function_name ,
            [f"{agent.role}'s final thinking: {thinking}" for agent, thinking in zip(self.debate_agents, all_thinking[-1])],
            [f"{agent.role}'s final answer: {answer}" for agent, answer in zip(self.debate_agents, all_answers[-1])],
            mode="code_fill"
        )
        return final_result['solution'], self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-4o")
        llm_config = ModelsConfig.default().get("deepseek-chat")
        graph = MultiPersonaGraph(name="multi-persona", llm_config=llm_config, dataset="HumanEval")
        file_path = "examples/ags/data/baseline_data/human-eval.jsonl"
        samples = 1
        path = "examples/ags/data/baselines/general/humaneval"
        score, cost = await humaneval_evaluation(graph, file_path, samples, path, test=False)
        return score, cost
    
    import asyncio
    asyncio.run(main())
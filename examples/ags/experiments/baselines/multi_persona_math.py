from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.math import math_evaluation
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import List

DEBATE_INITIAL_PROMPT = """
{question}\nPlease reason step by step, the reason process can be put in the thinking field. At the end, provide the final answer in the answer field with the format "\\boxed{{<number>}}", where <number> is a math answer(an expression or number), without any additional information or explanation.
Make sure the output is wrapped with correct xml tags!
"""

DEBATE_PROMPT = """
{question}
Considering the solutions provided by other agents as additional suggestions, the reason process can be put in the thinking field. Please think carefully and provide an updated answer in the answer field with the format "\\boxed{{<number>}}", where <number> is a math answer(an expression or number), without any additional information or explanation.
Make sure the output is wrapped with correct xml tags!
"""

FINAL_DECISION_PROMPT = """
{question}
Considering all the thinking processes and answers:
{all_thinking}
{all_answers}

The thinking process can be put in the thinking field.
Please reason carefully and provide the final answer in the answer field with the format "\\boxed{{<number>}}", where <number> is a math answer(an expression or number), without any additional information or explanation.
Make sure the output is wrapped with correct xml tags!
"""

class DebateOp(BaseModel):
    thinking: str = Field(default="", description="thinking process")
    answer: str = Field(default="", description="answer")

class FinalDecisionOp(BaseModel):
    thinking: str = Field(default="", description="final thinking process")
    solution: str = Field(default="", description="final answer")

class DebateAgent(Operator):
    def __init__(self, llm: LLM, name: str, role: str):
        super().__init__(name, llm)
        self.role = role

    async def __call__(self, problem: str, context: List[str] = None, mode: str = None):
        role_prompt = f"You are a {self.role}. Based on your professional knowledge and thinking style,"
        if context is None:
            prompt = role_prompt + DEBATE_INITIAL_PROMPT.format(question=problem)
        else:
            prompt = role_prompt + DEBATE_PROMPT.format(question=problem) + "\n".join(context)
        
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(DebateOp).fill(**fill_kwargs)
        return node.instruct_content.model_dump()

class FinalDecisionAgent(Operator):
    def __init__(self, llm: LLM, name: str = "FinalDecision"):
        super().__init__(name, llm)

    async def __call__(self, problem: str, all_thinking: List[str], all_answers: List[str], mode: str = None):
        prompt = FINAL_DECISION_PROMPT.format(
            question=problem,
            all_thinking="\n".join(all_thinking),
            all_answers="\n".join(all_answers)
        )
        fill_kwargs = {"context": prompt, "llm": self.llm}
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
                'Innovative Math Thinker - Math PhD',
                'Critical Reasoning Expert - Math Professor',
                'Computational Thinking Specialist - Math And Computer Science Researcher'
            ])
        ]
        self.final_decision_agent = FinalDecisionAgent(self.llm)

    async def __call__(self, problem):
        max_round = 2
        all_thinking = [[] for _ in range(max_round)]
        all_answers = [[] for _ in range(max_round)]

        for r in range(max_round):
            for i, agent in enumerate(self.debate_agents):
                if r == 0:
                    result = await agent(problem, mode="context_fill")
                else:
                    context = [f"{agent.role}'s previous round thinking: {all_thinking[r-1][i]}"] + \
                              [f"{self.debate_agents[j].role}'s thinking: {all_thinking[r-1][j]}" for j in range(len(self.debate_agents)) if j != i]
                    result = await agent(problem, context, mode="context_fill")
                all_thinking[r].append(result["thinking"])
                all_answers[r].append(result["answer"])

        final_result = await self.final_decision_agent(
            problem,
            [f"{agent.role}'s final thinking: {thinking}" for agent, thinking in zip(self.debate_agents, all_thinking[-1])],
            [f"{agent.role}'s final answer: {answer}" for agent, answer in zip(self.debate_agents, all_answers[-1])],
            mode="context_fill"
        )
        return final_result, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        graph = MultiPersonaGraph(name="multi-persona", llm_config=llm_config, dataset="MATH")
        file_path = "examples/ags/data/math_test.jsonl"
        samples = 0
        path = "examples/ags/data/baselines/general/math"
        score = await math_evaluation(graph, file_path, samples, path,test=True)
        return score

    import asyncio
    asyncio.run(main())
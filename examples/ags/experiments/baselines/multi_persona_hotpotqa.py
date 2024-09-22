from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.hotpotqa import hotpotqa_evaluation
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import List

DEBATE_INITIAL_PROMPT = """
Given a question and context, please think step by step and then solve this task.

Question: {question}
Context: {relevant_context}
"""

DEBATE_PROMPT = """
Given a question and context,

Question: {question}
Context: {relevant_context}

Considering the solutions provided by other agents as additional suggestions. Please think carefully and provide an updated answer.
"""

FINAL_DECISION_PROMPT = """
Given a question and context,

Question: {question}
Context: {relevant_context}

Considering all the thinking processes and answers:
{all_thinking}
{all_answers}
Please reason carefully and provide the final answer. Give the final answer in solution field. You MUST Keep the answer very concise in a few words, without any additional information.
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

    async def __call__(self, question: str, relevant_context: str, context: List[str] = None, mode: str = None):
        role_prompt = f"You are a {self.role}. Based on your professional knowledge and thinking style,"
        if context is None:
            prompt = role_prompt + DEBATE_INITIAL_PROMPT.format(question=question, relevant_context=relevant_context)
        else:
            prompt = role_prompt + DEBATE_PROMPT.format(question=question, relevant_context=relevant_context) + "\n".join(context)

        
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(DebateOp).fill(**fill_kwargs)
        return node.instruct_content.model_dump()

class FinalDecisionAgent(Operator):
    def __init__(self, llm: LLM, name: str = "FinalDecision"):
        super().__init__(name, llm)

    async def __call__(self, question: str, relevant_context: str, all_thinking: List[str], all_answers: List[str], mode: str = None):
        prompt = FINAL_DECISION_PROMPT.format(
            question = question,
            relevant_context = relevant_context,
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
                'Comprehensive Knowledge Maven - Information Scientist',
                'Analytical Insight Specialist - Cognitive Psychologist',
                'Fact Verification Expert - Data Analyst'
            ])
        ]
        self.final_decision_agent = FinalDecisionAgent(self.llm)

    async def __call__(self, question, relevant_context):
        max_round = 2
        all_thinking = [[] for _ in range(max_round)]
        all_answers = [[] for _ in range(max_round)]

        for r in range(max_round):
            for i, agent in enumerate(self.debate_agents):
                if r == 0:
                    result = await agent(question, relevant_context, mode="context_fill")
                else:
                    context = [f"{agent.role}'s previous round thinking: {all_thinking[r-1][i]}"] + \
                              [f"{self.debate_agents[j].role}'s thinking: {all_thinking[r-1][j]}" for j in range(len(self.debate_agents)) if j != i]
                    result = await agent(question, relevant_context, context, mode="context_fill")
                all_thinking[r].append(result["thinking"])
                all_answers[r].append(result["answer"])

        final_result = await self.final_decision_agent(
            question,
            relevant_context,
            [f"{agent.role}'s final thinking: {thinking}" for agent, thinking in zip(self.debate_agents, all_thinking[-1])],
            [f"{agent.role}'s final answer: {answer}" for agent, answer in zip(self.debate_agents, all_answers[-1])],
            mode="context_fill"
        )
        return final_result["solution"], self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        graph = MultiPersonaGraph(name="multi-persona", llm_config=llm_config, dataset="HotpotQA")

        file_path = "examples/ags/data/hotpotqa.jsonl"   #相对路径有问题 等着再改
        samples = 250 # 250 for validation, 1000 for test
        path = "examples/ags/data/baselines/general/hotpotqa" #相对路径有问题 等着再改

        score = await hotpotqa_evaluation(graph, file_path, samples, path, test=True)
        return score

    import asyncio
    asyncio.run(main())
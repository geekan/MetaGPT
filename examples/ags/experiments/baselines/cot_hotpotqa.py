from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.hotpotqa import hotpotqa_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Tuple

HOTPOTQA_PROMPT = """
问题: {question}

上下文:
{context}

请一步步思考,并在最后给出你的答案和支持性句子。使用XML标签包裹内容。
"""

class GenerateOp(BaseModel):
    answer: str = Field(default="", description="问题的答案")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, question: str, context: str, mode: str = None) -> Tuple[str, str]:
        prompt = HOTPOTQA_PROMPT.format(question=question, context=context)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response["answer"]

class CoTSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)

    async def __call__(self, question: str, context: str) -> Tuple[str, str]:
        answer = await self.cot_generate(question, context, mode="context_fill")
        return answer, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="HotpotQA")
        file_path = "examples/ags/data/hotpotqa.jsonl"
        samples = 50 # TODO 选择前1000条跑实验
        path = "examples/ags/data/baselines/general/hotpotqa"
        score = await hotpotqa_evaluation(graph, file_path, samples, path)
        return score

    import asyncio 
    asyncio.run(main())
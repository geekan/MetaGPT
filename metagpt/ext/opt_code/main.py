from metagpt.ext.opt_code.memory.aflow_memory import AFlowMemory
from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.opt_code.search_algorithm.aflow_search import AFlowSearch
from metagpt.ext.opt_code.optimizer.aflow_agent import AFlowAgent
from metagpt.ext.opt_code.evaluator.hotpotqa import HotpotQAEvaluator
import asyncio


if __name__ == "__main__":
    init_code = """
class Workflow:
    def __init__(
        self,
        name: str,
        llm_config,
        dataset: DatasetType,
    ) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        self.custom = operator.Custom(self.llm)

    async def __call__(self, problem: str):
        solution = await self.custom(input=problem, instruction=prompt_custom.PROMPT)
        return solution['response'], self.llm.cost_manager.total_cost
    """
    init_prompt = """
PROMPT = \"\"\"
Please think step by step.
\"\"\"
"""

    mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
    claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

    memory = AFlowMemory(init_code, init_prompt, "HotpotQA", ["Custom", "ScEnsemble", "AnswerGenerate"])
    search = AFlowSearch(memory, "HotpotQA")

    optimize_agent = AFlowAgent(claude_llm_config)
    evaluator = HotpotQAEvaluator("metagpt/ext/opt_code/data/hotpotqa_validate.jsonl", "metagpt/ext/opt_code/data/hotpotqa_test.jsonl", mini_llm_config)
    asyncio.run(search.search(optimize_agent, evaluator, 2))
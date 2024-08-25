import asyncio

from pydantic import BaseModel, Field

from metagpt.actions.action_node import ActionNode
from metagpt.configs.models_config import ModelsConfig
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

deepseek_llm_config = ModelsConfig.default().get("deepseek-coder")
deepseek_llm = create_llm_instance(deepseek_llm_config)
deepseek_llm.cost_manager = CostManager()
claude_llm_config = ModelsConfig.default().get("claude-3.5-sonnet")
claude_llm = create_llm_instance(claude_llm_config)

# TODO 思考一下，如何每次都去创建新实例，从而保证每次计数的一致。
# llm.cost_manager = data.llm.cost_manager


class GenerateCodeSolution(BaseModel):
    solution: str = Field(default="", description="A description of the solution")
    thought: str = Field(
        default="",
        description="Shortly explain why this solution correctly solves the problem. Be specific and detailed regarding the problem rules and goals.",
    )


GENERATE_ON_CONTEXT_PROMPT = """
Please generate a solution for the following problem based on the provided context:

### Problem Description
{problem_description}
"""


async def main():
    prompt = GENERATE_ON_CONTEXT_PROMPT.format(
        problem_description="Janet\u2019s ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?"
    )
    node = await ActionNode.from_pydantic(GenerateCodeSolution).fill(
        context=prompt, llm=deepseek_llm, mode="context_fill"
    )
    response = node.instruct_content.model_dump()

    print(deepseek_llm.cost_manager.total_cost)

    return response


if __name__ == "__main__":
    print(asyncio.run(main()))

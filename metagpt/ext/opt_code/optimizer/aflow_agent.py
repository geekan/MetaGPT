from metagpt.ext.opt_code.optimizer.base_agent import Agent
from metagpt.ext.opt_code.utils.aflow import WORKFLOW_INPUT, WORKFLOW_CUSTOM_USE, WORKFLOW_OPTIMIZE_PROMPT
from metagpt.actions.action_node import ActionNode
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import random


class GraphOptimize(BaseModel):
    modification: str = Field(default="", description="modification")
    graph: str = Field(default="", description="graph")
    prompt: str = Field(default="", description="prompt")


class AFlowAgent(Agent):
    def __init__(self, llm_config):
        super().__init__(llm_config)

    async def _generate_code(self, reference_code, context):
        experience_str = "Failure experience: " + "\n".join(context["experience"]["failure"]) \
                       + "\nSuccess experience: " + "\n".join(context["experience"]["success"])

        if len(context["log_data"]) > 3:
            # random pick 3 logs
            context["log_data"] = random.sample(context["log_data"], 3)
        
        graph_input = WORKFLOW_INPUT.format(
            experience=experience_str,
            score=context["score"],
            graph=reference_code,
            prompt=context["prompt"],
            operator_description=context["operator_description"],
            type=context["type"],
            log=context["log_data"],
        )

        graph_system = WORKFLOW_OPTIMIZE_PROMPT.format(type=context["type"])

        prompt = graph_input + WORKFLOW_CUSTOM_USE + graph_system
        graph_optimize_node = await ActionNode.from_pydantic(GraphOptimize).fill(
                context=prompt, mode="xml_fill", llm=self.optimizer
            )
        while True:
            try:
                response = await self._get_response_from_llm(graph_optimize_node)
            except Exception as e:
                print(e)
                continue
            
            if self.check_modification(context["experience"], response["modification"]):
                break

        return response
    
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1), retry=retry_if_exception_type(Exception), reraise=True)
    async def _get_response_from_llm(self, action_node):
        response = action_node.instruct_content.model_dump()
        return response


    def check_modification(self, experience_data, modification):
        if experience_data:
            for key, value in experience_data["failure"].items():
                if value == modification:
                    return False
            for key, value in experience_data["success"].items():
                if value == modification:
                    return False
            return True
        else:
            return True
from metagpt.ext.opt_code.search_algorithm.tree_search import TreeSearch
from metagpt.ext.opt_code.memory.sela_memory import SelaMemory, SelaNode
from metagpt.provider.llm_provider_registry import create_llm_instance
import json
import re
import numpy as np

def clean_json_from_rsp(text):
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        json_str = "\n".join(matches)
        return json_str
    else:
        return ""

CHANGE_INSTRUCTION = """
# Original instruction
{instruction}

# Insights
{insights}

Rewrite the original instruction according to the insights 
(If the original instruction involves splitting the data, ensure that your insights are integrated with the data split instructions, 
rather than replacing them.)

# Expected Output Hard Format
```json
{{
    "Original Instruction": "original instruction",
    "New Instruction": "new instruction"
}}
```
"""

REFLECTION_SYSTEM_MSG = "As a Kaggle Grandmaster competing in a challenge, your task is to suggest potential evolutionary improvements that could enhance the performance of the baseline code."


class SelaSearch(TreeSearch):
    def __init__(self, configs):
        super().__init__(configs)

    async def _initialize(self, node, global_context):
        global_context["insights_pool"] = self.load_insight_pool(self.configs["exp_pool_path"])
        self.llm = create_llm_instance(self.configs["llm_config"])

    def select(self, memory):
        def uct(node: SelaNode, memory: SelaMemory):
            n_visits = node.visit_count if node.visit_count else memory.c_unvisited
            avg_value = node.avg_value() if node.visit_count else node.reward / memory.c_unvisited
            return avg_value + memory.c_explore * np.sqrt(np.log(node.parent.visit_count) / n_visits)
        
        if len(memory.node_list) == 1:
            return memory.node_list[0]
        
        all_children = memory.node_list[1:]
        node = max(all_children, key=lambda x: uct(x, memory))

        memory.node_pointer = memory.node_list.index(node)
        return node

    def load_insight_pool(self, file_path):
        data = self.load_json_data(file_path)
        return data

    def load_json_data(self, json_dir):
        with open(json_dir, "r") as file:
            json_data = json.load(file)
            return json_data

    def get_next_instruction(self, node: SelaNode):
        return node.tasks[node.state["start_task_id"]].instruction

    async def expand_and_prepare(self, node: SelaNode, memory):
        if node.visit_count > 0:
            return await super().expand_and_prepare(node, memory)
        else:
            return node, self._prepare(node)

    async def _expand(self, node: SelaNode, memory: SelaMemory):
        original_instruction = self.get_next_instruction(node)

        new_instructions = await self.generate_new_instructions(
            original_instruction=original_instruction,
            max_num=self.configs["max_children"]
        )

        for new_instruction in new_instructions:
            child = node.extend_child(new_instruction)
            memory.node_list.append(child)

        return np.random.choice(node.children)
    
    def _prepare(self, node: SelaNode):
        pass

    async def generate_new_instructions(self, original_instruction, max_num):
        data = self.global_context["insights_pool"]
        new_instructions = []

        for i in range(max_num):
            if len(data) == 0:
                insights = "No insights available"
            else:
                item = data[i]
                insights = item["Analysis"]
            
            prompt = CHANGE_INSTRUCTION.format(instruction = original_instruction, insights = insights)

            response = await self.llm.aask(prompt, system_msgs=[REFLECTION_SYSTEM_MSG]
            )
            response = clean_json_from_rsp(response)
            new_instruction = json.loads(response)["New Instruction"]

            new_instructions.append(new_instruction)
        
        return new_instructions
    
    def _update_global_context(self, node, results):
        pass
import json
import os
import random

from expo.utils import clean_json_from_rsp, load_data_config, mcts_logger
from metagpt.llm import LLM
from metagpt.schema import Message

REFLECTION_SYSTEM_MSG = "As a Kaggle grandmaster participating in a competition, you need to analyze your experience and propose evolutionary points that are more likely to improve the performance of baseline code."

CHANGE_INSTRUCTION = """
# Original instruction
{instruction}

# Insights
{insights}

Rewrite the original instruction according to the insights

# Expected Output Hard Format
```json
{{
    "Original Instruction": "original instruction",
    "New Instruction": "new instruction"
}}
```
"""

DATA_CONFIG = load_data_config()


class InstructionGenerator:
    data_config = DATA_CONFIG

    @staticmethod
    def load_json_data(json_dir):
        with open(json_dir, "r") as file:
            json_data = json.load(file)
            return json_data

    @staticmethod
    def _random_sample(analysis, num_samples):
        return random.sample(analysis, num_samples)

    @staticmethod
    def sample_instruction_set(data):
        data_dict = {}
        for item in data:
            task_id = item["task_id"]
            if task_id not in data_dict:
                data_dict[task_id] = []
            data_dict[task_id].append(item)
        instruction_set = []
        for task_id in sorted(data_dict.keys()):
            instruction_set.append(random.choice(data_dict[task_id]))
        return instruction_set

    @staticmethod
    def format_output(rsp):
        rsp_list = []
        new_data = []
        rsp_list.append(rsp)
        for item in rsp_list:
            item_dict = json.loads(item)
            data = {
                "Insights": item_dict,
            }
            new_data.append(data)
        return new_data

    @staticmethod
    def load_analysis_pool(file_path, use_fixed_insights, task_id=None):
        data = InstructionGenerator.load_json_data(file_path)
        if use_fixed_insights:
            current_directory = os.path.dirname(__file__)
            fixed_insights = InstructionGenerator.load_json_data(f"{current_directory}/fixed_insights.json")
            data.extend(fixed_insights)
        for item in data:
            if "task_id" not in item:
                raise ValueError("task_id is not found in the analysis pool")

        if task_id:
            data = [item for item in data if int(item["task_id"]) == int(task_id)]
        return data

    @staticmethod
    async def generate_new_instructions(
        task_id, original_instruction, max_num, file_path, ext_info=None, use_fixed_insights=False
    ):
        data = InstructionGenerator.load_analysis_pool(
            file_path, task_id=task_id, use_fixed_insights=use_fixed_insights
        )
        new_instructions = []
        if len(data) == 0:
            mcts_logger.log("MCTS", f"No insights available for task {task_id}")
            # return [original_instruction]  # Return the original instruction if no insights are available
        for i in range(max_num):
            if len(data) == 0:
                insights = "No insights available"
            else:
                item = data[i]
                insights = item["Analysis"]
            new_instruction = await InstructionGenerator.generate_new_instruction(
                original_instruction, insights, ext_info
            )
            new_instructions.append(new_instruction)
        return new_instructions

    @staticmethod
    async def generate_new_instruction(original_instruction, insights, ext_info):
        prompt = CHANGE_INSTRUCTION.format(instruction=original_instruction, insights=insights)
        llm = LLM()
        context = llm.format_msg([Message(content=prompt, role="user")])
        llm_response = await llm.aask(context, system_msgs=[REFLECTION_SYSTEM_MSG])
        rsp = clean_json_from_rsp(llm_response)
        new_instruction = json.loads(rsp)["New Instruction"]
        return new_instruction

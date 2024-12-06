import json
import os
import random
from difflib import SequenceMatcher

from metagpt.ext.sela.insights.solution_designer import SolutionDesigner
from metagpt.ext.sela.utils import clean_json_from_rsp, load_data_config, mcts_logger
from metagpt.llm import LLM
from metagpt.schema import Message

REFLECTION_SYSTEM_MSG = "As a Kaggle Grandmaster competing in a challenge, your task is to suggest potential evolutionary improvements that could enhance the performance of the baseline code."

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

DATA_CONFIG = load_data_config()


class InstructionGenerator:
    def __init__(self, state, use_fixed_insights, from_scratch, data_config=None):
        self.data_config = data_config if data_config is not None else DATA_CONFIG
        self.state = state
        self.file_path = state["exp_pool_path"]
        if state["custom_dataset_dir"]:
            with open(f"{state['custom_dataset_dir']}/description.md", "r", encoding="utf-8") as file:
                self.dataset_info = file.read()
        else:
            dataset_info_path = (
                f"{self.data_config['datasets_dir']}/dataset_info.json"
                if self.data_config["datasets_dir"].rpartition("/")[-1] == state["dataset_config"]["dataset"]
                else f"{self.data_config['datasets_dir']}/{state['dataset_config']['dataset']}/dataset_info.json"
            )

            with open(dataset_info_path, "r") as file:
                self.dataset_info = json.load(file)
        self.use_fixed_insights = use_fixed_insights
        self.proposer = SolutionDesigner()
        if self.file_path is None:
            self.from_scratch = True
        else:
            self.from_scratch = from_scratch

    async def initialize(self):
        if self.from_scratch:
            self.insight_pool = await self.generate_solutions_from_scratch(self.dataset_info, self.state["task"])
        else:
            self.insight_pool = self.load_insight_pool(self.file_path, self.use_fixed_insights)

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
    def load_insight_pool(file_path, use_fixed_insights, task_id=None):
        data = InstructionGenerator.load_json_data(file_path)
        if use_fixed_insights:
            current_directory = os.path.dirname(__file__)
            fixed_insights = InstructionGenerator.load_json_data(f"{current_directory}/fixed_insights.json")
            data.extend(fixed_insights)
        for item in data:
            if "task_id" not in item:
                raise ValueError("task_id is not found in the insight_pool")

        if task_id:
            data = [item for item in data if int(item["task_id"]) == int(task_id)]
        return data

    async def generate_new_instructions(self, task_id, original_instruction, max_num, ext_info=None):
        data = self.insight_pool
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

    async def propose_new_insights(self, solution, score):
        new_insights = await self.proposer.propose_insights(solution, score)
        added_insights = self.add_insight(new_insights)
        return added_insights

    async def generate_solutions_from_scratch(self, dataset_info, dataset_name):
        insight_pool = await self.proposer.generate_solutions(dataset_info, dataset_name, save_analysis_pool=False)
        return insight_pool

    def add_insight(self, new_insights):
        added_insights = []
        for new_insight in new_insights:
            if not self.is_similar_to_existing(new_insight):
                added_insights.append(new_insight)
                self.insight_pool.append(new_insight)
        return added_insights

    def is_similar_to_existing(self, new_insight, similarity_threshold=0.8):
        for existing_insight in self.insight_pool:
            similarity = self.calculate_similarity(new_insight["Analysis"], existing_insight["Analysis"])
            if similarity > similarity_threshold:
                return True
        return False

    @staticmethod
    def calculate_similarity(text1, text2):
        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    async def generate_new_instruction(original_instruction, insights, ext_info):
        prompt = CHANGE_INSTRUCTION.format(instruction=original_instruction, insights=insights)
        llm = LLM()
        context = llm.format_msg([Message(content=prompt, role="user")])
        llm_response = await llm.aask(context, system_msgs=[REFLECTION_SYSTEM_MSG])
        rsp = clean_json_from_rsp(llm_response)
        new_instruction = json.loads(rsp)["New Instruction"]
        return new_instruction

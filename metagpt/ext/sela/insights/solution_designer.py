import json

from metagpt.ext.sela.utils import clean_json_from_rsp, load_data_config
from metagpt.llm import LLM

DATA_CONFIG = load_data_config()


DATASET_DESCRIPTION_SELA_PROMPT = """
# Dataset Description
{dataset}

# Dataset Metadata
{metadata}

# Dataset Head
{head}
"""

DATASET_DESCRIPTION_CUSTOM_PROMPT = """
# Dataset Description
{dataset_description}
"""

DATASET_INSIGHT_PROMPT = """
{description}

# Instruction
Propose insights to help improve the performance of the model on this dataset.
The insights should be proposed based on the dataset description with different task types.
Each task type should have at least 5 insights.
Make sure each method is diverse enough and can be implemented separately.
Be specific about models' choices, ensemble and tuning techniques, and preprocessing & feature engineering techniques.
Your model choices should be advanced enough to be helpful.

# Format
```json
[
    {{
        "task_type": "EDA",
        "insights": [
            "insight1",
            "insight2",
            "insight3",
            ...
            "insightN"
        ]   
    }},
    {{
        "task_type": "Data Preprocessing",
        "insights": [
            "insight1",
            "insight2",
            "insight3",
            ...
            "insightN"
        ]   
    }},
    {{
        "task_type": "Feature Engineering",
        "insights": [
            "insight1",
            "insight2",
            "insight3",
            ...
            "insightN"
        ]   
    }},
    {{
        "task_type": "Model Training",
        "insights": [
            "insight1",
            "insight2",
            "insight3",
            ...
            "insightN"
        ]   
    }}
]
```
"""


INSIGHT_PROPOSAL_PROMPT = """
You are an AI assistant tasked with analyzing a machine learning solution and proposing new insights to improve its performance. Given the current solution code and development score, suggest innovative approaches to enhance the model.

Current Solution Code:
{solution_code}

Development Score: {dev_score}

Based on this information, propose 3-5 new insights across different aspects of the machine learning pipeline (Data Preprocessing, Feature Engineering, and Model Training). Your insights should be specific, actionable, and have the potential to improve the model's performance.

Please format your response as a JSON array with the following structure:
[

    {{
        "task_type": "Data Preprocessing",
        "insights": [
            "insight1",
            "insight2"
        ]
    }},
    {{
        "task_type": "Feature Engineering",
        "insights": [
            "insight1",
            "insight2"
        ]
    }},
    {{
        "task_type": "Model Training",
        "insights": [
            "insight1",
            "insight2"
        ]
    }}
]
"""


KEY_DATASET_FEATURES = [
    "NumberOfClasses",
    "NumberOfFeatures",
    "NumberOfInstances",
    "NumberOfInstancesWithMissingValues",
    "NumberOfMissingValues",
    "NumberOfNumericFeatures",
    "NumberOfSymbolicFeatures",
]

TASK_TO_ID = {"EDA": 1, "Data Preprocessing": 2, "Feature Engineering": 3, "Model Training": 4, "Model Evaluation": 5}


class SolutionDesigner:
    data_dir: str = DATA_CONFIG["datasets_dir"]

    async def generate_solutions(self, dataset_info, dataset_name, save_analysis_pool=True):
        llm = LLM()
        if type(dataset_info) == dict:
            description_prompt = DATASET_DESCRIPTION_SELA_PROMPT.format(
                dataset=dataset_info["description"],
                metadata=self.metadata_builder(dataset_info["metadata"]),
                head=dataset_info["df_head"],
            )
        else:
            description_prompt = DATASET_DESCRIPTION_CUSTOM_PROMPT.format(dataset_description=dataset_info)
        context = DATASET_INSIGHT_PROMPT.format(description=description_prompt)
        rsp = await llm.aask(context)
        rsp = clean_json_from_rsp(rsp)
        analysis_pool = self.process_analysis_pool(json.loads(rsp))
        if save_analysis_pool:
            dataset_path = f"{self.data_dir}/{dataset_name}"
            self.save_analysis_pool(dataset_path, analysis_pool)
        return analysis_pool

    async def propose_new_insights(self, solution, score):
        llm = LLM()
        context = INSIGHT_PROPOSAL_PROMPT.format(solution_code=solution, dev_score=score)
        rsp = await llm.aask(context)
        rsp = clean_json_from_rsp(rsp)
        new_insights = self.process_analysis_pool(json.loads(rsp))
        return new_insights

    def process_analysis_pool(self, insights_rsp):
        analysis_pool = []
        for task_type_insights in insights_rsp:
            task_type = task_type_insights["task_type"]
            for insight in task_type_insights["insights"]:
                analysis_pool.append({"Analysis": insight, "Category": task_type, "task_id": TASK_TO_ID[task_type]})
        return analysis_pool

    def metadata_builder(self, qualities):
        metadata = {}
        for key in KEY_DATASET_FEATURES:
            metadata[key] = qualities.get(key, "N/A")
        metadata_text = json.dumps(metadata, indent=4)
        return metadata_text

    def save_analysis_pool(self, dataset_path, analysis_pool):
        fpath = f"{dataset_path}/ds_analysis_pool.json"
        with open(fpath, "w") as file:
            json.dump(analysis_pool, file, indent=4)

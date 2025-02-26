import os

from metagpt.ext.sela.data.dataset import SPECIAL_INSTRUCTIONS
from metagpt.ext.sela.runner.mle_bench.instructions import (
    ADDITIONAL_NOTES,
    INSTRUCTIONS,
    INSTRUCTIONS_OBFUSCATED,
)

MLE_BENCH_FILES = ["description.md", "description_obfuscated.md"]


MLE_REQUIREMENTS = """
{instructions}

{additonal_notes}

COMPETITION INSTRUCTIONS
------

{task_description}

## More Instructions
- You should split the training data into train and dev set with a seed of 42.
- You should use the dev set to improve your model. Print the final dev set score after training.
- output_dir: {output_dir}
- Besides `submission.csv`, you should also save your `test_predictions.csv` and `dev_predictions.csv` in the output directory.
- Note that `test_predictions.csv` should be identical to `submission.csv`.
- Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. {special_instruction}
**Do not make any plots or visualizations.**
"""


def get_mle_task_id(dataset_dir):
    return dataset_dir.split("/")[-3]


def get_mle_is_lower_better(task):
    from mlebench.data import get_leaderboard
    from mlebench.registry import registry

    competition = registry.get_competition(task)
    competition_leaderboard = get_leaderboard(competition)
    return competition.grader.is_lower_better(competition_leaderboard)


def get_mle_bench_requirements(dataset_dir, data_config, special_instruction, obfuscated=False):
    work_dir = data_config["work_dir"]
    task = get_mle_task_id(dataset_dir)
    output_dir = f"{work_dir}/{task}"
    final_output_dir = f"{work_dir}/submission"
    os.makedirs(output_dir, exist_ok=True)
    if special_instruction:
        special_instruction = SPECIAL_INSTRUCTIONS[special_instruction]
    else:
        special_instruction = ""
    if obfuscated:
        instructions = INSTRUCTIONS_OBFUSCATED.format(dataset_dir=dataset_dir, output_dir=final_output_dir)
        task_file = "description_obfuscated.md"
    else:
        instructions = INSTRUCTIONS.format(dataset_dir=dataset_dir, output_dir=output_dir)
        task_file = "description.md"

    with open(os.path.join(dataset_dir, task_file), encoding="utf-8") as f:
        task_description = f.read()
    mle_requirement = MLE_REQUIREMENTS.format(
        instructions=instructions,
        additonal_notes=ADDITIONAL_NOTES,
        task_description=task_description,
        output_dir=output_dir,
        special_instruction=special_instruction,
    )
    print(mle_requirement)
    return mle_requirement

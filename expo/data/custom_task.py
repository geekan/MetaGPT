import os

from expo.experimenter.mle_bench.instructions import (
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
- output_dir: {output_dir}
- Besides `submission.csv`, you should also save your output in the output directory.
- You should split the training data into train and dev set.
- Save the prediction results of BOTH the dev set and test set in `dev_predictions.csv` and `test_predictions.csv` respectively in the output directory. They should be in the same format as the `submission.csv`.
- Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. 
**Do not make any plots or visualizations.**
"""


def get_mle_task_id(dataset_dir):
    return dataset_dir.split("/")[-3]


def get_mle_bench_requirements(dataset_dir, data_config, obfuscated=False):
    work_dir = data_config["work_dir"]
    task = get_mle_task_id(dataset_dir)
    output_dir = f"{work_dir}/{task}"
    final_output_dir = f"{work_dir}/submission"
    os.makedirs(output_dir, exist_ok=True)

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
    )
    print(mle_requirement)
    return mle_requirement

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

"""


def get_mle_bench_requirements(dataset_dir, data_config, obfuscated=False):
    if obfuscated:
        instructions = INSTRUCTIONS_OBFUSCATED
        task_file = "description_obfuscated.md"
    else:
        instructions = INSTRUCTIONS
        task_file = "description.md"

    with open(os.path.join(dataset_dir, task_file)) as f:
        task_description = f.read()
    mle_requirement = MLE_REQUIREMENTS.format(
        instructions=instructions, additonal_notes=ADDITIONAL_NOTES, task_description=task_description
    )
    return mle_requirement

import json
import os
import traceback
from pathlib import Path

import fire
import numpy as np
from datasets import load_dataset, load_from_disk
from make_datasets.utils import extract_diff
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm.auto import tqdm

from data.inference.const import SCIKIT_LEARN_IDS
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.utils import count_string_tokens
from metagpt.utils.recovery_util import save_history

# Replace with your own
MAX_TOKEN = 128000


@retry(wait=wait_random_exponential(min=30, max=600), stop=stop_after_attempt(5))
async def call_chat(inputs, interpreter):
    """
    Calls the openai API to generate completions for the given inputs.

    Args:
    inputs (str): The inputs to generate completions for.
    interpreter (DataInterpreter): The data interpreter to use for execution.
    """
    requirement = "Please rewrite the code and generate test case to address the issues existing in the repository. If the test code passes, it is considered that the execution code has passed and use the `git diff` command to output the patch based on the correct code."
    system_messages = inputs.split("\n", 1)[0]
    user_message = inputs.split("\n", 1)[1]
    try:
        await interpreter.run([requirement, system_messages, user_message])
        return interpreter.get_last_cell_source()
    except Exception as e:
        logger.error(f"Error: {e}\nInputs: {inputs}")
        traceback.print_exc()
        raise e


async def openai_inference(
    test_dataset,
    model_name_or_path,
    output_file,
    existing_ids,
    use_reflection,
):
    """
    Runs inference on a dataset using the openai API.

    Args:
    test_dataset (datasets.Dataset): The dataset to run inference on.
    model_name_or_path (str): The name or path of the model to use.
    output_file (str): The path to the output file.
    existing_ids (set): A set of ids that have already been processed.
    """
    test_dataset = test_dataset.filter(
        lambda x: count_string_tokens(x["text"], model_name_or_path) <= MAX_TOKEN,
        desc="Filtering",
        load_from_cache_file=False,
    )
    basic_args = {
        "model_name_or_path": model_name_or_path,
    }
    print(f"Filtered to {len(test_dataset)} instances")
    with open(output_file, "a+") as f:
        for datum in tqdm(test_dataset, desc=f"Inference for {model_name_or_path}"):
            di = DataInterpreter(use_reflection=use_reflection)
            instance_id = datum["instance_id"]

            if instance_id in existing_ids:
                continue
            output_dict = {"instance_id": instance_id}
            output_dict.update(basic_args)
            output_dict["text"] = f"{datum['text']}\n\n"
            response = await call_chat(
                output_dict["text"],
                di,
            )
            logger.info(f"Final response: {response}")
            save_history(di)
            output_dict["full_output"] = response
            output_dict["model_patch"] = extract_diff(response)
            print(json.dumps(output_dict), file=f, flush=True)


async def main(
    dataset_name_or_path,
    split="test",
    model_name_or_path=config.llm.model,
    output_dir="outputs",
    use_reflection=True,
):
    """
    Performs inference on SWE-bench dataset using the Data Interpreter.

    Args:
    dataset_name_or_path: HuggingFace dataset name or local path
    split: Dataset split to use (default: test)
    model_name_or_path: Name of the model to use (default: config.llm.model)
    param output_dir: Path to the output directory (default: outputs)
    """
    model_nickname = Path(model_name_or_path).name if isinstance(model_name_or_path, Path) else model_name_or_path
    output_file = f"{model_nickname}__{dataset_name_or_path.split('/')[-1]}__{split}"
    output_file = Path(output_dir, output_file + ".jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Will write to {output_file}")
    existing_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            for line in f:
                data = json.loads(line)
                instance_id = data["instance_id"]
                existing_ids.add(instance_id)
    logger.info(f"Read {len(existing_ids)} already completed ids from {output_file}")
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
    if split not in dataset:
        raise ValueError(f"Invalid split {split} for dataset {dataset_name_or_path}")
    dataset = dataset[split]
    lens = np.array(list(map(len, dataset["text"])))
    dataset = dataset.select(np.argsort(lens))

    if len(existing_ids) > 0:
        dataset = dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering out existing ids",
            load_from_cache_file=False,
        )
    if len(SCIKIT_LEARN_IDS) > 0:
        dataset = dataset.filter(
            lambda x: x["instance_id"] in SCIKIT_LEARN_IDS,
            desc="Filtering out subset_instance_ids",
            load_from_cache_file=False,
        )
    inference_args = {
        "test_dataset": dataset,
        "model_name_or_path": model_name_or_path,
        "output_file": output_file,
        "existing_ids": existing_ids,
        "use_reflection": use_reflection,
    }
    if model_name_or_path.startswith("gpt"):
        await openai_inference(**inference_args)
    else:
        raise ValueError(f"Invalid model name or path {model_name_or_path}")
    logger.info("Done!")


if __name__ == "__main__":
    fire.Fire(main)

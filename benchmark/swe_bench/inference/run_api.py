import json
from pathlib import Path

import fire
from tqdm.auto import tqdm

from benchmark.swe_bench.data.load_dataset import load_oracle_dataset
from benchmark.swe_bench.inference.run_agent import run_instance
from benchmark.swe_bench.utils.utils import check_existing_ids, extract_diff
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.utils import count_string_tokens

# Replace with your own
MAX_TOKEN = 128000


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
    logger.info(f"Filtered to {len(test_dataset)} instances")
    data = []
    with open(output_file, "a+") as f:
        for datum in tqdm(test_dataset, desc=f"Inference for {model_name_or_path}"):
            instance_id = datum["instance_id"]

            if instance_id in existing_ids:
                continue
            version = datum["version"]
            repo = datum["repo"]
            repo_prefix = repo.replace("/", "__")
            output_dict = {"instance_id": instance_id}
            output_dict.update(basic_args)
            output_dict["text"] = f"{datum['text']}\n\n"
            logger.info(f"{repo_prefix}_{version}")
            data.append(f"{repo_prefix}_{version}")

            response = await run_instance(instance=datum, use_reflection=use_reflection)
            if response is None:
                continue
            logger.info(f"Final response: {response}")

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
    print(output_file.absolute())
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Will write to {output_file}")

    # check existing results
    existing_ids = check_existing_ids(output_file)
    # load dataset
    dataset = load_oracle_dataset(dataset_name_or_path)

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

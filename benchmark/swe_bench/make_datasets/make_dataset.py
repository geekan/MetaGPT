# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os
from pathlib import Path

from tqdm.auto import tqdm

from benchmark.swe_bench.inference.const import TESTBED
from benchmark.swe_bench.make_datasets.make_instance import prompt_style_2_edits_only
from benchmark.swe_bench.utils.parse_diff import filter_changed_line
from benchmark.swe_bench.utils.repo_utils import EnvManager
from metagpt.logs import logger


def reset_task_env(instance: dict = {}):
    # reset the env via git reset and git checkout
    env_manager = EnvManager(testbed=TESTBED)

    patch = instance["patch"]
    repo = instance["repo"]
    instance["version"]
    repo_prefix = repo.replace("/", "__")
    repo_path = os.path.join(env_manager.testbed, repo_prefix)

    if not os.path.exists(repo_path):
        return patch, repo, None
    os.chdir(repo_path)
    if not env_manager.reset_task_env(instance=instance):
        return patch, repo, None

    return patch, repo, repo_path


def reset_and_copy(instance: dict = {}):
    patch, repo, repo_path = reset_task_env(instance)
    if repo_path is None:
        return
    env_manager = EnvManager(testbed=TESTBED)
    repo_prefix = repo.replace("/", "__")
    version = instance["version"]
    destination_path = os.path.join(repo_path, f"{repo_prefix}__{version}")
    env_manager.copy_repo(source_path=repo_path, destination_path=destination_path)


def make_oracle_collapsed_instance(instance):
    # for each instance, reset task env
    patch, repo, repo_path = reset_task_env(instance)
    if repo_path is None:
        return
    file_changes = filter_changed_line(patch)
    prompt = prompt_style_2_edits_only(instance, Path(repo_path), list(file_changes.keys()))
    logger.info(prompt)
    # todo: save output
    return {}


def make_oracle_collapsed_dataset(dataset):
    for datum in tqdm(dataset, desc="Inference "):
        make_oracle_collapsed_instance(instance=datum)
    # todo: save output

# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pandas as pd

from metagpt.const import METAGPT_ROOT

SUBSET_DATASET = METAGPT_ROOT / "benchmark" / "swe_bench" / "sub_swebench_dataset" / "sub_swebench.csv"
SUBSET_DATASET_SKLERARN = METAGPT_ROOT / "benchmark" / "sub_swebench_dataset" / "scikit-learn-68.csv"
TESTBED = METAGPT_ROOT / "benchmark" / "swe_bench" / "data" / "repos"

# SCIKIT_LEARN_IDS: A list of instance identifiers from 'sub_swebench.csv' within SUBSET_DATASET.
# This collection represents a subset specifically related to scikit-learn content.
SCIKIT_LEARN_IDS = [
    "scikit-learn__scikit-learn-11578",
    "scikit-learn__scikit-learn-10297",
    "scikit-learn__scikit-learn-25747",
    "scikit-learn__scikit-learn-15512",
    "scikit-learn__scikit-learn-15119",
    "scikit-learn__scikit-learn-10870",
    "scikit-learn__scikit-learn-15100",
    "scikit-learn__scikit-learn-14496",
    "scikit-learn__scikit-learn-14890",
    "scikit-learn__scikit-learn-10428",
    "scikit-learn__scikit-learn-25744",
    "scikit-learn__scikit-learn-11542",
    "scikit-learn__scikit-learn-10198",
    "scikit-learn__scikit-learn-10459",
]

MATPLOTLIB_IDS = [
    "matplotlib__matplotlib-24362",
    "matplotlib__matplotlib-20584",
    "matplotlib__matplotlib-23188",
    "matplotlib__matplotlib-24403",
    # 'matplotlib__matplotlib-21443',
    # 'matplotlib__matplotlib-23047'
]


def read_subset_instance(path=SUBSET_DATASET, tag="scikit-learn"):
    try:
        df = pd.read_excel(path)
        pass_filters = df["instance_id_pass"].tolist()
        fail_filters = df["instance_id_fail"].tolist()
        pass_filters = [s for s in pass_filters if tag in s]
        fail_filters = [s for s in fail_filters if tag in s]
        subset_instance = pass_filters + fail_filters

        return subset_instance
    except FileNotFoundError:
        print(f"File not found: {path}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    print(read_subset_instance(tag="matplotlib__matplotlib"))

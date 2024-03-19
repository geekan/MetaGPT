# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pandas as pd

from metagpt.const import METAGPT_ROOT

SUBSET_DATASET = METAGPT_ROOT / "sub_swebench_dataset" / "sub_swebench.csv"
SUBSET_DATASET_SKLERARN = METAGPT_ROOT / "sub_swebench_dataset" / "scikit-learn-68.csv"

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


def read_sub_set_instance(path=SUBSET_DATASET, tag="scikit-learn"):
    try:
        df = pd.read_excel(path)
        # Filter for instances containing the tag in either column
        pass_filter = df["instance_id_pass"].str.contains(tag, na=False)
        fail_filter = df["instance_id_fail"].str.contains(tag, na=False)

        # Combine the filters using | (OR operator) for efficiency
        combined_filter = pass_filter | fail_filter

        # Apply combined filter and select the specific columns
        filtered_df = df[combined_filter][["instance_id_pass", "instance_id_fail"]]

        # Flatten the DataFrame into a list and remove NaN values
        subset_instance = filtered_df.stack().dropna().tolist()

        return subset_instance
    except FileNotFoundError:
        print(f"File not found: {path}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

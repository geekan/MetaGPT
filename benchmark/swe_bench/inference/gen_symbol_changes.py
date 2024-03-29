import json
from pathlib import Path

import pandas as pd
from pandas import Series

from benchmark.swe_bench.inference.const import SCIKIT_LEARN_IDS
from benchmark.swe_bench.make_datasets.make_dataset import reset_task_env
from benchmark.swe_bench.utils.ast_parser import ASTParser
from benchmark.swe_bench.utils.parse_diff import filter_changed_line
from metagpt.const import METAGPT_ROOT

# your parquet file path
PARQUET_FILE = f"{METAGPT_ROOT}/benchmark/sub_swebench_dataset/oracle_test.parquet"
# symbol changes list file path
SYMBOL_CHANGES_FILE = f"{METAGPT_ROOT}/benchmark/sub_swebench_dataset/symbol_changes_list.json"


def gen_symbol_changes(swe_row: Series):
    # row is a row that matches the format of the original swe data set.
    patch, repo, repo_path = reset_task_env(swe_row)
    patch = swe_row["patch"]
    file_changes = filter_changed_line(patch)
    pr_symbol_changes = []
    for file_name, changes in file_changes.items():
        if not str(file_name).endswith(".py"):
            continue
        code_path = Path(repo_path) / file_name
        if not code_path.exists():
            continue
        ap = ASTParser(str(file_name), code_path, set(i["line"] for i in changes))
        ap.traverse(ap.tree)
        pr_symbol_changes.append(ap.symbol_changes)

    return pr_symbol_changes


if __name__ == "__main__":
    # read parquet file
    df = pd.read_parquet(PARQUET_FILE)
    mg_symbol_changes = [
        {
            "file": [],
            "class": [],
            "function": [],
            "import": [],
            "global": [],
            "method": [],
        }
    ]
    filtered_df = df[df["instance_id"].isin(SCIKIT_LEARN_IDS)]
    symbol_changes_list = []
    for i, row in filtered_df.iterrows():
        instance_id = row["instance_id"]
        symbol_changes = gen_symbol_changes(row)
        sc_list = []
        for sc in symbol_changes:
            function = sc["function"]
            class_and_method = [sc["class"][i] + ", " + sc["method"][i] for i in range(len(sc["method"]))]
            if function or class_and_method:
                sc_list.append(function + class_and_method)

        symbol_changes_list.append({instance_id: sc_list})

    with open(SYMBOL_CHANGES_FILE, "w") as f:
        json.dump(symbol_changes_list, f)

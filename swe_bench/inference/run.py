# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import runpy
import sys

original_argv = sys.argv.copy()

try:
    # 设置你想要传递给脚本的命令行参数
    dataset_path = "SWE-bench_oracle"  # "SWE-bench_bm25_27K"  # "SWE-bench_13k"
    sys.argv = ["run_api.py", "--dataset_name_or_path", f"princeton-nlp/{dataset_path}", "--output_dir", "./outputs"]
    # 执行脚本
    runpy.run_path(path_name="run_api.py", run_name="__main__")
finally:
    # 恢复原始的sys.argv以避免对后续代码的潜在影响
    sys.argv = original_argv

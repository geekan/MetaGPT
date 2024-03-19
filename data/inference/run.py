# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import runpy
import sys

original_argv = sys.argv.copy()

try:
    # 设置你想要传递给脚本的命令行参数
    sys.argv = ["run_api.py", "--dataset_name_or_path", "princeton-nlp/SWE-bench_oracle", "--output_dir", "./outputs"]
    # 执行脚本
    runpy.run_path(path_name="run_api.py", run_name="__main__")
finally:
    # 恢复原始的sys.argv以避免对后续代码的潜在影响
    sys.argv = original_argv

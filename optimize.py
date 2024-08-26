# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Experiment of graph optimization


from examples.ags.w_action_node.optimizer import Optimizer
from metagpt.configs.models_config import ModelsConfig

# 配置实验参数
dataset = "Gsm8K"  # 数据集选择为GSM8K
sample = 6  # 采样数量
q_type = "math"  # 问题类型为数学
optimized_path = "examples/ags/w_action_node/optimized"  # 优化结果保存路径

# 初始化LLM模型
deepseek_llm_config = ModelsConfig.default().get("deepseek-coder")
claude_llm_config = ModelsConfig.default().get("claude-3.5-sonnet")

# 初始化操作符列表
gsm8k_operators = [
    "Generate",
    "ContextualGenerate",
    "Format",
    "Review",
    "Revise",
    "FuEnsemble",
    "MdEnsemble",
    "ScEnsemble",
    "Rephrase",
]

# 创建优化器实例
optimizer = Optimizer(
    dataset=dataset,
    opt_llm_config=claude_llm_config,
    exec_llm_config=deepseek_llm_config,
    operators=gsm8k_operators,
    optimized_path=optimized_path,
    sample=sample,
    q_type=q_type,
)

# 运行优化器
optimizer.optimize("Graph")

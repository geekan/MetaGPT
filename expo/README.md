# Expo


## Instruction

- 下载数据集：https://deepwisdom.feishu.cn/drive/folder/RVyofv9cvlvtxKdddt2cyn3BnTc?from=from_copylink


## Examples

### Run Base DI
  
`python run_experiment.py --exp_mode base --task titanic`

### Run DI RandExp

- Single insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode single`

- Set insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode set`



### Run DI MCTS
`python run_experiment.py --exp_mode mcts --task titanic --rollout 5`

If the dataset has reg metric, remember to use `--low_is_better`
`python run_experiment.py --exp_mode mcts --task househouse_prices --rollout 5 --low_is_better`


## Code and Configs Explanation

`datasets.yaml` 提供数据集对应的指标和基础提示词

`data.yaml` 继承了`datasets.yaml`以及一些路径信息，需要将`datasets_dir`指到数据集合集的根目录下

完整的DI提示词参考`dataset.py`中的`generate_task_requirement`函数


## Evaluation

`evaluation.py` 提供pred和原始的gt（1D iterable）以及需要使用的metric，返回evaluation score


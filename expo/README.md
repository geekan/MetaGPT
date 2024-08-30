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

`python run_experiment.py --exp_mode mcts --task househouse_prices --rollout 5 --low_is_better`





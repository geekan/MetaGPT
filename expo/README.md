# Expo




## 1. Data Preparation

- 下载数据集：https://deepwisdom.feishu.cn/drive/folder/RVyofv9cvlvtxKdddt2cyn3BnTc?from=from_copylink
- 修改`data.yaml`的`datasets_dir`为数据集合集根目录存储位置


## 2. Configs

### Data Config

`datasets.yaml` 提供数据集对应的指标和基础提示词

`data.yaml` 继承了`datasets.yaml`以及一些路径信息，需要将`datasets_dir`指到数据集合集的根目录下


### LLM Config

```
llm:
  api_type: 'openai'
  model: deepseek-coder
  base_url: "https://oneapi.deepwisdom.ai/v1"
  api_key: sk-xxx
  temperature: 0.5
```

### Budget
实验轮次 k = 10, 20


### 提示词使用

- 通过执行`dataset.py`中的`generate_task_requirement`函数获取提示词
- 每一个数据集里有`dataset_info.json`，里面的内容需要提供给baselines以保证公平


## 3. Evaluation

运行各个框架，运行后框架需要提供Dev和Test的`dev_predictions.csv`和`test_predictions.csv`， column name为target

- 使用`CustomExperimenter`
```
experimenter = CustomExperimenter(task="titanic")
score_dict = experimenter.evaluate_pred_files(dev_pred_path, test_pred_path)
```

## 4. Baselines
### DS Agent
提供github链接，并说明使用的命令以及参数设置


### AIDE
提供github链接，并说明使用的命令以及参数设置

### Autogluon
#### Setup
```
pip install -U pip
pip install -U setuptools wheel

CPU version of pytorch has smaller footprint - see installation instructions in
pytorch documentation - https://pytorch.org/get-started/locally/
pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu

pip install autogluon
```

提供github链接，并说明使用的命令以及参数设置

### Base DI 
For setup, check 5.

- `python run_experiment.py --exp_mode base --task titanic --num_experiments 10`


### DI RandomSearch
For setup, check 5.

- Single insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode single`

- Set insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode set`


## 5. DI MCTS

### Run DI MCTS

#### Setup
In the root directory, 

```
pip install -e .

cd expo

pip install -r requirements.txt
```

#### Run

- `python run_experiment.py --exp_mode mcts --task titanic --rollout 5`

If the dataset has reg metric, remember to use `--low_is_better`:

- `python run_experiment.py --exp_mode mcts --task househouse_prices --rollout 5 --low_is_better`












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


### Prompt Usage

- 通过执行`dataset.py`中的`generate_task_requirement`函数获取提示词
  - 非DI-based方法设置`is_di=False`
  - `data_config`用`utils.DATA_CONFIG`
- 每一个数据集里有`dataset_info.json`，里面的内容需要提供给baselines以保证公平（`generate_task_requirement`已经默认提供）


## 3. Evaluation

运行各个框架，运行后框架需要提供Dev和Test的`dev_predictions.csv`和`test_predictions.csv`，每个csv文件只需要单个名为target的列

- 使用`CustomExperimenter`
```
experimenter = CustomExperimenter(task="titanic")
score_dict = experimenter.evaluate_pred_files(dev_pred_path, test_pred_path)
```

## 4. Baselines
### DS Agent
```
git clone https://github.com/guosyjlu/DS-Agent.git
```

将其deployment/generate.py line46-48行部分修改如下（目的是用deepseek而非GPT的API）：
```python
messages = [{"role": "user", "content": prompt}]

if 'gpt' in llm:
    response = openai.ChatCompletion.create(**{"messages": messages,**raw_request})
    raw_completion = response["choices"][0]["message"]["content"]
    
elif llm == 'deepseek-coder':
    from openai import OpenAI
    client = OpenAI(
        api_key="yours", 
        base_url="https://oneapi.deepwisdom.ai/v1"
    )
    response = client.chat.completions.create(
        model="deepseek-coder",
        messages=[
            # {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        stream=False
    )
    raw_completion = response.choices[0].message.content

completion = raw_completion.split("```python")[1].split("```")[0]
```

修改完后在新建一个`deployment/test.sh` 分别运行下列两行，`$TASK` 是你要测试的task name
```
python -u generate.py --llm deepseek-coder --task $TASK --shot 1 --retrieval > "$TASK".txt 2>&1 

python -u evaluation.py --path "deepseek-coder_True_1" --task $TASK --device 0  > "$TASK"_eval.txt 2>&1 
```

### AIDE

#### Setup

```
git clone https://github.com/WecoAI/aideml.git
```

修改 `aideml/aide/utils/config.yaml` 内容如下

```yaml
# path to the task data directory
data_dir: null

# either provide a path to a plaintext file describing the task
desc_file: null
# or provide the task goal (and optionally evaluation information) as arguments
goal: null
eval: null

log_dir: logs
workspace_dir: workspaces

# whether to unzip any archives in the data directory
preprocess_data: True
# whether to copy the data to the workspace directory (otherwise it will be symlinked)
# copying is recommended to prevent the agent from accidentally modifying the original data
copy_data: True

exp_name: null # a random experiment name will be generated if not provided

# settings for code execution
exec:
  timeout: 3600
  agent_file_name: runfile.py
  format_tb_ipython: False

# agent hyperparams
agent:
  # how many improvement iterations to run
  steps: 10
  # whether to instruct the agent to use CV (set to 1 to disable)
  k_fold_validation: 1
  # whether to instruct the agent to generate a prediction function
  expose_prediction: False
  # whether to provide the agent with a preview of the data
  data_preview: True

  # LLM settings for coding
  code:
    model: deepseek-coder
    temp: 0.5

  # LLM settings for evaluating program output / tracebacks
  feedback:
    model: deepseek-coder
    temp: 0.5

  # hyperparameters for the tree search
  search:
    max_debug_depth: 3
    debug_prob: 0.5
    num_drafts: 5
```

由于 deepseek 完全兼容 OpenAI 的 API，修改`base_url`为`自己的url`，`api_key`为`自己的key`即可

```
export OPENAI_API_KEY="自己的key"
export OPENAI_BASE_URL="自己的url"
```

修改`aideml/aide/backend/__init__.py` 30 行内容如下：

```python
model_kwargs = model_kwargs | {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if "claude-" in model:
        query_func = backend_anthropic.query
    else:
        query_func = backend_openai.query
```

由于 deepseekV2.5 不再支持 system message 使用 function call，修改 `aideml/aide/agent.py` 312 行内容如下：

```python
response = cast(
            dict,
            query(
                system_message=None,
                user_message=prompt,
                func_spec=review_func_spec,
                model=self.acfg.feedback.model,
                temperature=self.acfg.feedback.temp,
            ),
        )
```

修改完后

```
cd aideml
pip install -e .
```

#### Run

运行下面脚本获取运行结果，在当前目录下将生成一个 log 文件夹以及 workspace 文件夹
log 文件夹中将包含实验使用配置以及生成方案记录，workspace 文件夹下将保存 aide 最后生成的结果文件

```
python experimenter/aide.py
```

### Autogluon
#### Setup
```
pip install -U pip
pip install -U setuptools wheel
pip install autogluon

python run_expriment.py --exp_mode autogluon --task fashion_mnist
```

提供github链接，并说明使用的命令以及参数设置
### AutoSklearn
#### System requirements
auto-sklearn has the following system requirements:

- Linux operating system (for example Ubuntu)

- Python (>=3.7)

- C++ compiler (with C++11 supports)

In case you try to install Auto-sklearn on a system where no wheel files for the pyrfr package are provided (see here for available wheels) you also need:

- SWIG [(get SWIG here).](https://www.swig.org/survey.html)

For an explanation of missing Microsoft Windows and macOS support please check the Section [Windows/macOS compatibility](https://automl.github.io/auto-sklearn/master/installation.html#windows-macos-compatibility).

#### Setup
```
pip install auto-sklearn
```

#### Run
```
python run_experiment.py --exp_mode autosklearn --task titanic
```

### Base DI 
For setup, check 5.

- `python run_experiment.py --exp_mode base --task titanic --num_experiments 10`
- Ask DI to use AutoGluon: `--special_instruction ag`
- Ask DI to use the stacking ensemble method: `--special_instruction stacking`




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

- `python run_experiment.py --exp_mode mcts --task titanic --rollout 10`

If the dataset has reg metric, remember to use `--low_is_better`:

- `python run_experiment.py --exp_mode mcts --task househouse_prices --rollout 10 --low_is_better`


In addition to the generated insights, include the fixed insights saved in `expo/insights/fixed_insights.json`
- `--use_fixed_insights`
  


#### Ablation Study

**DI RandomSearch**

- Single insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode single`

- Set insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode set`










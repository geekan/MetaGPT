# SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning




## 1. Data Preparation

- Download Datasets：https://deepwisdom.feishu.cn/drive/folder/RVyofv9cvlvtxKdddt2cyn3BnTc?from=from_copylink


## 2. Configs

### Data Config

`datasets.yaml` Provide base prompts, metrics, target columns for respective datasets

- Modify `datasets_dir` to the root directory of all the datasets in `data.yaml`


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
Experiment rollouts k = 5, 10, 20


### Prompt Usage

- Use the function `generate_task_requirement` in `dataset.py` to get task requirement.
  - If the method is non-DI-based, set `is_di=False`.
  - Use `utils.DATA_CONFIG` as `data_config`


## 3. SELA

### Run SELA

#### Setup
In the root directory, 

```
pip install -e .

cd expo

pip install -r requirements.txt
```

#### Run

- `python run_experiment.py --exp_mode mcts --task titanic --rollouts 10`

If the dataset has reg metric, remember to use `--low_is_better`:

- `python run_experiment.py --exp_mode mcts --task house_prices --rollouts 10 --low_is_better`


In addition to the generated insights, include the fixed insights saved in `expo/insights/fixed_insights.json`
- `--use_fixed_insights`
  


#### Ablation Study

**DI RandomSearch**

- Single insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode single`

- Set insight
`python run_experiment.py --exp_mode aug --task titanic --aug_mode set`


## 4. Evaluation

Each baseline needs to produce `dev_predictions.csv`和`test_predictions.csv`. Each csv file only needs a `target` column.

- Use the function `evaluate_score` to evaluate.


## 5. Baselines
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

修改 `aideml/aide/utils/config.yaml` 其中的 `step` `k_fold_validation` `code model` `feedback model` 参数如下

```yaml
# agent hyperparams
agent:
  # how many improvement iterations to run
  steps: 10
  # whether to instruct the agent to use CV (set to 1 to disable)
  k_fold_validation: 1
  # LLM settings for coding
  code:
    model: deepseek-coder
    temp: 0.5

  # LLM settings for evaluating program output / tracebacks
  feedback:
    model: deepseek-coder
    temp: 0.5
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

```

For Tabular data:
```
python run_expriment.py --exp_mode autogluon --task {task_name}
```
For Multimodal data:
```
python run_expriment.py --exp_mode autogluon --task {task_name} --is_multimodal
```
Replace {task_name} with the specific task you want to run.


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
For setup, check 4.
- `python run_experiment.py --exp_mode base --task titanic --num_experiments 10`
- Specifically instruct DI to use AutoGluon: `--special_instruction ag`
- Specifically instruct DI to use the stacking ensemble method: `--special_instruction stacking`












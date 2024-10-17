# SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning




## 1. Data Preparation

- Download Datasets：https://deepwisdom.feishu.cn/drive/folder/RVyofv9cvlvtxKdddt2cyn3BnTc?from=from_copylink
- Download and prepare datasets from scratch:
  ```
  cd expo/data
  python dataset.py --save_analysis_pool
  python hf_data.py --save_analysis_pool
  ```

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

- `python run_experiment.py --exp_mode mcts --task house-prices --rollouts 10 --low_is_better`


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

#### MLE-Bench
**Note: mle-bench requires python 3.11 or higher**
```
git clone https://github.com/openai/mle-bench.git
cd mle-bench
pip install -e .
```

```
mlebench prepare -c <competition-id> --data-dir <dataset-dir-save-path>
```

Enter the following command to run the experiment:
```
python run_experiment.py --exp_mode mcts --custom_dataset_dir <dataset-dir-save-path/prepared/public> --rollouts 10 --from_scratch --role_timeout 3600
```


## 5. Baselines
### DS Agent
```
git clone https://github.com/guosyjlu/DS-Agent.git
```

Modify the following lines in deployment/generate.py (lines 46-48) as shown below (the purpose is to use deepseek instead of OpenAI's API):
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

After making the changes, create a new `deployment/test.sh` and run the following two lines separately, where `$TASK` is the name of the task you want to test
```
python -u generate.py --llm deepseek-coder --task $TASK --shot 1 --retrieval > "$TASK".txt 2>&1 

python -u evaluation.py --path "deepseek-coder_True_1" --task $TASK --device 0  > "$TASK"_eval.txt 2>&1 
```

### AIDE

#### Setup

```
git clone https://github.com/WecoAI/aideml.git
```

Modify `aideml/aide/utils/config.yaml`:

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

Since Deepseek is compatible to OpenAI's API, change `base_url` into `your own url`，`api_key` into `your api key`

```
export OPENAI_API_KEY="your api key"
export OPENAI_BASE_URL="your own url"
```

Modify `aideml/aide/backend/__init__.py`'s line 30 and below:

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

Since deepseekV2.5 no longer supports system message using function call, modify `aideml/aide/agent.py`'s line 312:

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

Modify and install:

```
cd aideml
pip install -e .
```

#### Run

Run the following script to get the running results, a `log` folder and a `workspace` folder will be generated in the current directory
The `log` folder will contain the experimental configuration and the generated scheme, and the `workspace` folder will save the final results generated by aide

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
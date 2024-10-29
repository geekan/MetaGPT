# SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning

## 1. Data Preparation

You can either download the datasets from the link or prepare the datasets from scratch.
- **Download Datasets:** [Dataset Link](https://deepwisdom.feishu.cn/drive/folder/RVyofv9cvlvtxKdddt2cyn3BnTc?from=from_copylink)
- **Download and prepare datasets from scratch:**
    ```bash
    cd data
    python dataset.py --save_analysis_pool
    python hf_data.py --save_analysis_pool
    ```

## 2. Configurations

### Data Config

- **`datasets.yaml`:** Provide base prompts, metrics, and target columns for respective datasets.
- **`data.yaml`:** Modify `datasets_dir` to the base directory of all prepared datasets.

### LLM Config

```yaml
llm:
  api_type: 'openai'
  model: deepseek-coder
  base_url: "https://your_base_url"
  api_key: sk-xxx
  temperature: 0.5
```


## 3. SELA

### Run SELA

#### Setup

```bash
pip install -e .

cd metagpt/ext/sela

pip install -r requirements.txt
```

#### Running Experiments

- **Examples:**
    ```bash
    python run_experiment.py --exp_mode mcts --task titanic --rollouts 10
    python run_experiment.py --exp_mode mcts --task house-prices --rollouts 10 --low_is_better
    ```

#### Parameters

- **`--rollouts`:** The number of rollouts.
- **`--use_fixed_insights`:** Include fixed insights saved in `expo/insights/fixed_insights.json`.
- **`--low_is_better`:** Use this if the dataset has a regression metric.
- **`--from_scratch`:** Generate a new insight pool based on the dataset before running MCTS.
- **`--role_timeout`:** Limits the duration of a single simulation (e.g., `10 rollouts with timeout 1,000` = max 10,000s).
- **`--max_depth`:** Set the maximum depth of MCTS (default is 4).
- **`--load_tree`:** Load an existing MCTS tree if the previous experiment was interrupted.
    - Example:
      ```bash
      python run_experiment.py --exp_mode mcts --task titanic --rollouts 10
      ```
    - To resume:
      ```bash
      python run_experiment.py --exp_mode mcts --task titanic --rollouts 7 --load_tree
      ```

### Ablation Study

**RandomSearch**

- **Use a single insight:**
    ```bash
    python run_experiment.py --exp_mode rs --task titanic --rs_mode single
    ```

- **Use a set of insights:**
    ```bash
    python run_experiment.py --exp_mode rs --task titanic --rs_mode set
    ```
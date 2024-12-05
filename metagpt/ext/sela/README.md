# SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning


Official implementation for paper [SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning](https://arxiv.org/abs/2410.17238).


SELA is an innovative system that enhances Automated Machine Learning (AutoML) by integrating Monte Carlo Tree Search (MCTS) with LLM-based agents. Traditional AutoML methods often generate low-diversity and suboptimal code, limiting their effectiveness in model selection and ensembling. SELA addresses these challenges by representing pipeline configurations as trees, enabling agents to intelligently explore the solution space and iteratively refine their strategies based on experimental feedback.

## 1. Data Preparation

You can either download the datasets from the link or prepare the datasets from scratch.
- **Download Datasets:** [Dataset Link](https://drive.google.com/drive/folders/151FIZoLygkRfeJgSI9fNMiLsixh1mK0r?usp=sharing)
- **Download and prepare datasets from scratch:**
    ```bash
    # cd to SELA
    python data/dataset.py --save_analysis_pool
    python data/hf_data.py --save_analysis_pool
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

## 4. Citation
Please cite our paper if you use SELA or find it cool or useful! 

```bibtex
@misc{chi2024selatreesearchenhancedllm,
      title={SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning}, 
      author={Yizhou Chi and Yizhang Lin and Sirui Hong and Duyi Pan and Yaying Fei and Guanghao Mei and Bangbang Liu and Tianqi Pang and Jacky Kwok and Ceyao Zhang and Bang Liu and Chenglin Wu},
      year={2024},
      eprint={2410.17238},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2410.17238}, 
}
```

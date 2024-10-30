# SELA: Tree-Search Enhanced LLM Agents for Automated Machine Learning

This document provides instructions for running baseline models. To start with, ensure that you prepare the datasets as instructed in `sela/README.md`.

## Baselines

### 1. AIDE

#### Setup

We use the AIDE version from September 30, 2024. Clone the repository and check out the specified commit:

```bash
git clone https://github.com/WecoAI/aideml.git
git checkout 77953247ea0a5dc1bd502dd10939dd6d7fdcc5cc
```


Modify `aideml/aide/utils/config.yaml` to set the following parameters:

```yaml
# agent hyperparams
agent:
  steps: 10  # Number of improvement iterations
  k_fold_validation: 1  # Set to 1 to disable cross-validation
  code:
    model: deepseek-coder
    temp: 0.5
  feedback:
    model: deepseek-coder
    temp: 0.5
  search:
    max_debug_depth: 3
    debug_prob: 0.5
    num_drafts: 5
```

Update your OpenAI API credentials in the environment:

```bash
export OPENAI_API_KEY="your api key"
export OPENAI_BASE_URL="your own url"
```

Modify `aideml/aide/backend/__init__.py` (line 30 and below):

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

Since Deepseek V2.5 no longer supports system messages using function calls, modify `aideml/aide/agent.py` (line 312):

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

Finally, install AIDE:

```bash
cd aideml
pip install -e .
```

#### Run

Execute the following script to generate results. A `log` folder (containing experimental configurations) and a `workspace` folder (storing final results) will be created:

```bash
python runner/aide.py
```

---

### 2. Autogluon

#### Setup

Install Autogluon:

```bash
pip install -U pip
pip install -U setuptools wheel
pip install autogluon==1.1.1
```

#### Run

For Tabular data:

```bash
python run_experiment.py --exp_mode autogluon --task {task_name}
```

For Multimodal data:

```bash
python run_experiment.py --exp_mode autogluon --task {task_name} --is_multimodal
```

Replace `{task_name}` with the specific task you want to run.

---

### 3. AutoSklearn

**Note:**
AutoSklearn requires:
- Linux operating system (e.g., Ubuntu)
- Python (>=3.7)
- C++ compiler (with C++11 support)

If installing on a system without wheel files for the `pyrfr` package, you also need:

- [SWIG](https://www.swig.org/survey.html)

Refer to the [Windows/macOS compatibility](https://automl.github.io/auto-sklearn/master/installation.html#windows-macos-compatibility) section for further details.

#### Setup

Install AutoSklearn:

```bash
pip install auto-sklearn==0.15.0
```

#### Run

Execute the following command for the Titanic task:

```bash
python run_experiment.py --exp_mode autosklearn --task titanic
```

---

### 4. Base Data Interpreter

Run the following command for the Titanic task:

```bash
python run_experiment.py --exp_mode base --task titanic --num_experiments 10
```

---

### 5. Custom Baselines

To run additional baselines:

- Each baseline must produce `dev_predictions.csv` and `test_predictions.csv` with a `target` column.
- Use the `evaluate_score` function for evaluation.
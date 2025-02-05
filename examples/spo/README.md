# SPO 🤖 | Self-Supervised Prompt Optimizer

An automated prompt engineering tool for Large Language Models (LLMs), designed for universal domain adaptation.

A next-generation prompt engineering system implementing **Self-Supervised Prompt Optimization (SPO)**. Achieves state-of-the-art performance with 17.8-90.9× higher cost efficiency than conventional methods. 🚀

## ✨ Core Advantages

- 💸 **Ultra-Low Cost** - _$0.15 per task optimization_
- 🏷️ **Zero Supervision** - _No ground truth/human feedback required_
- ⚡ **Universal Adaptation** - _Closed & open-ended tasks supported_
- 🔄 **Self-Evolving** - _Auto-optimization via LLM-as-judge mechanism_

## 🚀 Quick Start

### 1. Configure Your API Key ⚙️

Configure LLM parameters in `config/config2.yaml` (see `examples/aflow/config2.example.yaml` for reference)
### 2. Define Your Iteration template 📝

Create a Iteration template file `metagpt/ext/spo/settings/task_name.yaml`:
```yaml
prompt: |
  solve question.

requirements: |
  ...

count: None

faq:
  - question: |
      ...
    answer: |
      ...

  - question: |
      ...
    answer: |
      ...
```

### 3. Implement the Optimizer 🔧

我帮你完成这个 Readme 部分：

### 3. Implement the Optimizer 🔧

Use `metagpt/ext/spo/optimize.py` to execute:

```python
from metagpt.ext.spo.scripts.optimizer import Optimizer
from metagpt.ext.spo.scripts.utils.llm_client import SPO_LLM

if __name__ == "__main__":
    # Initialize LLM settings
    SPO_LLM.initialize(
        optimize_kwargs={"model": "claude-3-5-sonnet-20240620", "temperature": 0.7},
        evaluate_kwargs={"model": "gpt-4o-mini", "temperature": 0.3},
        execute_kwargs={"model": "gpt-4o-mini", "temperature": 0}
    )

    # Create and run optimizer
    optimizer = Optimizer(
        optimized_path="workspace",    # Output directory
        initial_round=1,               # Starting round
        max_rounds=10,                 # Maximum optimization rounds
        template="Poem.yaml",          # Template file
        name="Poem",                   # Project name
        iteration=True,                # Enable iteration mode
    )

    optimizer.optimize()
```

Or you can use command line interface:

```bash
python optimize.py [options]
```

Available command line options:
```
--optimize-model         Model for optimization (default: claude-3-5-sonnet-20240620)
--optimize-temperature  Temperature for optimization (default: 0.7)
--evaluate-model        Model for evaluation (default: gpt-4o-mini)
--evaluate-temperature  Temperature for evaluation (default: 0.3)
--execute-model         Model for execution (default: gpt-4o-mini)
--execute-temperature   Temperature for execution (default: 0)
--workspace            Output directory path (default: workspace)
--initial-round        Initial round number (default: 1)
--max-rounds          Maximum number of rounds (default: 10)
--template            Template file name (default: Poem.yaml)
--name                Project name (default: Poem)
--no-iteration        Disable iteration mode (iteration enabled by default)
```

For help:
```bash
python optimize.py --help
```
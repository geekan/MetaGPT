# AFlow: Automating Agentic Workflow Generation

AFlow is a framework for automatically generating and optimizing Agentic Workflows. It uses Monte Carlo tree search in a code-represented workflow space to find effective workflows, replacing manual development with machine effort. Our approach shows potential to outperform handcrafted workflows on various tasks.

[Read our paper on arXiv](https://arxiv.org/abs/2410.10762)

[Insert performance graph/image here]

## Framework Components

- **Node**: Basic unit of LLM invocation. See `action_node.py` for a flexible interface to control LLM, temperature, format, and prompt.
- **Operator**: Predefined combinations of Nodes to enhance search efficiency. Encapsulates common operations like Generate, Format, Review, Revise, Ensemble, Test, and Programmer.
- **Workflow**: A sequence of LLM-invoking nodes connected by edges. Can be represented as graphs, neural networks, or code to express various execution structures.
- **Optimizer**: Uses LLMs within a Monte Carlo Tree Search variant to explore and refine workflows. Iteratively selects, expands, evaluates, and updates workflows based on performance.
- **Evaluator**: Assesses workflow performance on given tasks. Provides feedback to guide the optimization process towards more effective workflows.

## Datasets

We provide implementations for [list datasets here]. 

Data is available at [link to data].

For custom tasks, [brief instructions or link to documentation].

## Quick Start

1. Configure your search in `optimize.py`:
   - Open `examples/aflow/scripts/optimize.py`
   - Set the following parameters:
     ```python
     dataset = "HumanEval"  # Choose from: "HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP" or your custom dataset name
     question_type = "code"  # Choose from: "math", "code", "qa"
     sample = 5  # Number of samples to use for optimization
     check_convergence = True  # Whether to check for convergence
     optimized_path = "path/to/optimized/workflows"  # Path to save optimized workflows
     initial_round = 1  # Starting round number
     max_rounds = 20  # Maximum number of optimization rounds
     ```
   - Adjust these parameters according to your specific requirements and dataset
2. Set up parameters in `config/config2.yaml` (see `examples/aflow/config2.example.yaml` for reference)
3. Set the operator you want to use in `optimize.py` and in `xxxx`
4. Download the init round of six datasets and put them in `xxxxxx`
5. Add your custom dataset and corresponding evaluation function:

- Create a new Python file in the `examples/aflow/benchmark/` directory, named `{custom_dataset_name}.py`
- Implement the following key functions in this new file:
  - `load_data`: for loading the dataset
  - `evaluate_problem`: for evaluating a single problem solution
  - `evaluate_all_problems`: for evaluating all problems
  - `save_results_to_csv`: for saving evaluation results
  - `optimize_{custom_dataset_name}_evaluation`: main evaluation function that integrates the above functionalities
- Add your custom dataset name and config val_list in `examples/aflow/scripts/evaluator.py`


## License

[License information]

## Citation

If you use AFlow in your research, please cite our paper:

```
@article{zhang2024aflow,
  title={AFlow: Automating Agentic Workflow Generation},
  author={Zhang, Jiayi and Xiang, Jinyu and Yu, Zhaoyang and Teng, Fengwei and Chen, Xionghui and Chen, Jiaqi and Zhuge, Mingchen and Cheng, Xin and Hong, Sirui and Wang, Jinlin and others},
  journal={arXiv preprint arXiv:2410.10762},
  year={2024}
}
```
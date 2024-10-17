# AFlow: Automating Agentic Workflow Generation

AFlow is a framework for automatically generating and optimizing Agentic Workflows. It uses Monte Carlo tree search in a code-represented workflow space to find effective workflows, replacing manual development with machine effort. Our approach shows potential to outperform handcrafted workflows on various tasks.

[Read our paper on arXiv](arxiv_link_here)

[Insert performance graph/image here]

## Framework Components

- **Node**: Basic unit of LLM invocation. See `action_node.py` for a flexible interface to control LLM, temperature, format, and prompt.
- **Operator**: Predefined combinations of Nodes to enhance search efficiency.
- **Workflow**: [Brief description needed]
- **Optimizer**: [Brief description needed]
- **Evaluator**: [Brief description needed]

## Datasets

We provide implementations for [list datasets here]. 

Data is available at [link to data].

For custom tasks, [brief instructions or link to documentation].

## Quick Start

1. Configure your search in `optimize.py`
2. Set up parameters in `config/config2.yaml` (see `examples/aflow/config2.example.yaml` for reference)

[Add any additional setup or running instructions]

## Contributing

[Instructions for contributing, if applicable]

## License

[License information]

## Citation

If you use AFlow in your research, please cite our paper:

```
[Citation details]
```

For more information, visit our [project website/documentation].
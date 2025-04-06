# MetaGPT Core

MetaGPT Core is the core component of the MetaGPT framework, providing basic functionality and tools. As the foundation of a multi-agent framework, this package provides the core tools and interfaces needed to build complex AI applications.

## Installation

```bash
pip install metagpt-core
```

## Features

- Provides the basic components and abstract interfaces of the MetaGPT framework
- Lightweight core library with minimal dependencies
- Can be used independently or integrated with the complete MetaGPT framework
- Contains core tool classes, basic AI interfaces, and extension systems

## Main Components

- Basic Abstraction Layer: Provides unified interfaces
- Tool Set: Common AI development tools
- Configuration System: Simplifies complex application configuration
- Memory Management: Efficiently processes data

## Optional Features

Install optional dependencies:

```bash
# Install development tools
pip install metagpt-core[dev]

# Install testing tools
pip install metagpt-core[test]

# Install pyppeteer support
pip install metagpt-core[pyppeteer]
```

## Dependencies

This package only includes minimal core dependencies:
- aiohttp: Async HTTP client/server
- loguru: Logging system
- pydantic: Data validation
- PyYAML: YAML parsing
- tenacity: Retry library
- tiktoken: Tokenization tool
- and other essential libraries

## License

MIT 
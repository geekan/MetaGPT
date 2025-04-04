# MetaGPT Poetry Scripts Guide

This directory contains scripts for building and installing MetaGPT using Poetry.

install poetry and loguru, before start: `pip install poetry loguru`

## Build Script (build.py)

`build.py` is used to build the MetaGPT package with Poetry, including both the core sub-package and the main package.

### Usage

```bash
python scripts/build.py
```

### Features

- Automatically cleans the dist directory to ensure clean build results
- Automatically detects the core package (metagpt/core) and builds it first
- Then builds the main package (metagpt)
- Outputs all build results to the dist directory in the project root
- Displays the filenames and sizes of the build results
- Records detailed logs during the build process

## Installation Script (install.py)

`install.py` is used to install MetaGPT and its dependencies using Poetry.

### Usage

```bash
python scripts/install.py [options]
```

### Options

- `--dev`: Install development dependencies
- `--groups GROUP1,GROUP2,...`: Install specified dependency groups, comma-separated, e.g., 'test,selenium'
- `--editable` or `-e`: Install in editable mode (recommended for development testing)
- `--core-only`: Only install the metagpt-core sub-package
- `--no-core`: Do not install the metagpt-core sub-package (only the main package)
- `--no-deps`: Do not install dependencies, only the project itself
- `--sync`: Synchronize all dependency versions in the lock file
- `--skip-env-check`: Skip virtual environment check

### Security Checks

- The script checks if it's running in a virtual environment
- After installation, an import test is performed to confirm successful installation

### Examples

Install the basic package:
```bash
python scripts/install.py
```

Install development dependencies:
```bash
python scripts/install.py --dev
```

Install specific dependency groups:
```bash
python scripts/install.py --groups test,selenium
```

Install in editable mode:
```bash
python scripts/install.py --editable
```

Only install the core package:
```bash
python scripts/install.py --core-only
```

Install the project while skipping dependencies:
```bash
python scripts/install.py --no-deps
```

## Dependencies

These scripts depend on the following Python packages:

- loguru: For logging
- poetry: For building and installation

If poetry is not installed, the script will automatically install it.

## Development Workflow Example

Here's a typical development workflow example:

1. After code changes, install in the development environment for testing:
   ```bash
   python scripts/install.py --dev
   ```

2. After testing is successful, build the distribution package:
   ```bash
   python scripts/build.py
   ```

3. View the build results:
   ```bash
   ls -l dist/
   ``` 
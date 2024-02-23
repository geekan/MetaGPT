#!/usr/bin/env bash
# python -m autopep8 .
python -m isort .
rm dist/* -f
python3 -m pip uninstall metagpt -y
python3 -m build
python3 -m pip install dist/*.whl
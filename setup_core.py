"""Setup script for MetaGPT core."""

from pathlib import Path

from setuptools import find_namespace_packages, setup

here = Path(__file__).resolve().parent
requirements = (here / "requirements_core.txt").read_text(encoding="utf-8").splitlines()

extras_require = {}

extras_require["test"] = [
    *set(i for j in extras_require.values() for i in j),
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-mock",
    "pytest-html",
    "pytest-xdist",
    "pytest-timeout",
    "connexion[uvicorn]~=3.0.5",
    "azure-cognitiveservices-speech~=1.31.0",
    "aioboto3~=12.4.0",
    "gradio==3.0.0",
    "google-api-core==2.17.1",
    "protobuf~=4.25.5",
    "pylint==3.0.3",
    "pybrowsers",
]

extras_require["pyppeteer"] = [
    "pyppeteer>=1.0.2"
]  # pyppeteer is unmaintained and there are conflicts with dependencies
extras_require["dev"] = (["pylint~=3.0.3", "black~=23.3.0", "isort~=5.12.0", "pre-commit~=3.6.0"],)

setup(
    name="metagpt-core",
    version="1.0.0",
    description="The core package of The Multi-Agent Framework",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/geekan/MetaGPT",
    author="Alexander Wu",
    author_email="alexanderwu@deepwisdom.ai",
    license="MIT",
    keywords="metagpt multi-agent multi-role programming gpt llm metaprogramming",
    packages=find_namespace_packages(include=["metagpt.core*"], exclude=["examples*", "tests*"]),
    # package_dir={"metagpt.core": "core"},
    python_requires=">=3.9, <3.12",
    install_requires=requirements,
    extras_require=extras_require,
    include_package_data=True,
)

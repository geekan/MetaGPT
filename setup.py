"""wutils: handy tools
"""
from codecs import open
from os import path
from setuptools import find_packages, setup, Command

import subprocess


class InstallMermaidCLI(Command):
    """A custom command to run `npm install -g @mermaid-js/mermaid-cli` via a subprocess."""

    description = 'install mermaid-cli'
    user_options = []

    def run(self):
        try:
            subprocess.check_call(['npm', 'install', '-g', '@mermaid-js/mermaid-cli'])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.output}")


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line]

setup(
    name="metagpt",
    version="0.1",
    description="The Multi-Role Meta Programming Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.deepwisdomai.com/pub/metagpt",
    author="Alexander Wu",
    author_email="alexanderwu@fuzhi.ai",
    license="Apache 2.0",
    keywords="metagpt multi-role multi-agent programming gpt llm",
    packages=find_packages(exclude=["contrib", "docs", "examples"]),
    python_requires=">=3.9",
    install_requires=requirements,
    cmdclass={
        'install_mermaid': InstallMermaidCLI,
    },
)

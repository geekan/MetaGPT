"""wutils: handy tools
"""
import subprocess
from codecs import open
from os import path

from setuptools import Command, find_packages, setup


class InstallMermaidCLI(Command):
    """A custom command to run `npm install -g @mermaid-js/mermaid-cli` via a subprocess."""

    description = "install mermaid-cli"
    user_options = []

    def run(self):
        try:
            subprocess.check_call(["npm", "install", "-g", "@mermaid-js/mermaid-cli"])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.output}")


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line]

setup(
    name="metagpt",
    version="0.4.0",
    description="The Multi-Role Meta Programming Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geekan/MetaGPT",
    author="Alexander Wu",
    author_email="alexanderwu@fuzhi.ai",
    license="Apache 2.0",
    keywords="metagpt multi-role multi-agent programming gpt llm",
    packages=find_packages(exclude=["contrib", "docs", "examples", "tests*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "playwright": ["playwright>=1.26", "beautifulsoup4"],
        "selenium": ["selenium>4", "webdriver_manager", "beautifulsoup4"],
        "search-google": ["google-api-python-client==2.94.0"],
        "search-ddg": ["duckduckgo-search==3.8.5"],
        "pyppeteer": ["pyppeteer>=1.0.2"],
    },
    cmdclass={
        "install_mermaid": InstallMermaidCLI,
    },
)

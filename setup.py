"""Setup script for MetaGPT."""
import subprocess

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


setup(
    packages=find_packages(exclude=["contrib", "docs", "examples", "tests*"]),
    cmdclass={
        "install_mermaid": InstallMermaidCLI,
    },
)

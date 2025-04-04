#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tool script for installing Mermaid CLI

This script provides functionality to install mermaid-cli in the MetaGPT environment,
similar to the InstallMermaidCLI command in setup.py, but adapted for Poetry environments.
"""

import subprocess
import sys

from metagpt.core.logs import logger


def install_mermaid_cli():
    """Install mermaid-cli

    Installs mermaid-cli via npm, enabling MetaGPT to generate diagrams.
    If installation fails, appropriate error messages and alternatives are provided.
    """
    try:
        # Check if npm is installed
        try:
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("npm is not installed. Please install Node.js to get npm: https://nodejs.org/")
            print("npm is not installed. Please install Node.js to get npm: https://nodejs.org/")
            return 1

        # Install mermaid-cli
        logger.info("Installing mermaid-cli...")
        print("Installing mermaid-cli...")
        subprocess.check_call(["npm", "install", "-g", "@mermaid-js/mermaid-cli"])

        logger.info("mermaid-cli installed successfully!")
        print("mermaid-cli installed successfully!")

        # Suggest alternatives to the user
        print("\nNote: MetaGPT also supports other diagram rendering engines:")
        print("1. playwright (recommended): pip install playwright && playwright install --with-deps chromium")
        print("2. pyppeteer: pip install pyppeteer")
        print("3. mermaid.ink: No installation required, only supports SVG and PNG formats")
        print("\nTo use these alternative engines, set in config2.yaml:")
        print("mermaid:\n  engine: playwright  # or pyppeteer, ink")

        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing mermaid-cli: {e}")
        print(f"Error installing mermaid-cli: {e}")
        print("\nPlease consider alternatives:")
        print("1. Local installation: npm install @mermaid-js/mermaid-cli")
        print("   Then set the path in config2.yaml: mermaid.path: './node_modules/.bin/mmdc'")
        print("2. Use other rendering engines:")
        print("   - playwright (recommended): pip install playwright && playwright install --with-deps chromium")
        print("   - pyppeteer: pip install pyppeteer")
        print("   - mermaid.ink: No installation required, only supports SVG and PNG formats")
        return 1


if __name__ == "__main__":
    sys.exit(install_mermaid_cli())

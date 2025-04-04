#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build metagpt packages using poetry
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from loguru import logger


def setup_logger():
    """Configure logger"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )


def clean_dist_dir(dist_dir: str):
    """Clean the dist directory

    Args:
        dist_dir: Path to the dist directory
    """
    if os.path.exists(dist_dir):
        logger.info(f"Cleaning dist directory: {dist_dir}")
        # Delete all files in the directory
        for file in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    logger.debug(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    logger.debug(f"Deleted directory: {file_path}")
            except Exception as e:
                logger.error(f"Deletion failed: {file_path}, Error: {e}")
    else:
        # Create directory
        os.makedirs(dist_dir)
        logger.info(f"Created dist directory: {dist_dir}")


def run_poetry_build(project_dir: str, output_dir: str = None) -> bool:
    """Run poetry build command to build packages

    Args:
        project_dir: Project root directory
        output_dir: Output directory (optional)

    Returns:
        bool: True if build successful, False otherwise
    """
    try:
        logger.info(f"Starting to build project: {os.path.basename(project_dir)}")
        # Build both wheel and sdist formats
        cmd = ["poetry", "build"]

        if output_dir:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            cmd.extend(["--output", output_dir])

        subprocess.run(cmd, cwd=project_dir, check=True, capture_output=True, text=True)

        logger.info(f"Build completed: {os.path.basename(project_dir)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Build failed: {e.stderr}")
        return False


def main():
    """Main function"""
    setup_logger()

    # Get project root directory
    project_root = Path(__file__).parent.parent.absolute()
    core_dir = os.path.join(project_root, "metagpt", "core")
    dist_dir = os.path.join(project_root, "dist")

    # Clean dist directory
    clean_dist_dir(dist_dir)

    # Check project structure
    if not os.path.exists(core_dir):
        logger.warning(f"Core directory does not exist: {core_dir}")
        if input("Continue building the main project? (y/n): ").lower() != "y":
            return
    else:
        # Build core project first
        logger.info("Starting to build core package...")
        if not run_poetry_build(core_dir, dist_dir):
            logger.error("Core project build failed, aborting main project build")
            if input("Force continue building the main project? (y/n): ").lower() != "y":
                return
        else:
            logger.info("Core project build successful")

    # Then build main project
    logger.info("Starting to build main project...")
    if run_poetry_build(project_root, dist_dir):
        logger.info(f"Main project build successful, output directory: {dist_dir}")
    else:
        logger.error("Main project build failed")

    # List built packages
    if os.path.exists(dist_dir):
        built_packages = os.listdir(dist_dir)
        if built_packages:
            logger.info(f"Built package files ({len(built_packages)}):")
            for package in built_packages:
                package_path = os.path.join(dist_dir, package)
                size_mb = os.path.getsize(package_path) / (1024 * 1024)
                logger.info(f"  - {package} ({size_mb:.2f} MB)")
            logger.info(f"All packages successfully built to: {dist_dir}")
        else:
            logger.warning("No built package files found")


if __name__ == "__main__":
    main()

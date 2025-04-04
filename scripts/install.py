#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Install metagpt and its dependencies using poetry
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


def setup_logger():
    """Configure logger"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Install MetaGPT using Poetry")

    parser.add_argument("--dev", action="store_true", help="Install development dependencies")

    parser.add_argument(
        "--groups", type=str, default="", help="Dependency groups to install, comma-separated, e.g. 'test,selenium'"
    )

    parser.add_argument("--editable", "-e", action="store_true", help="Install in editable mode")

    parser.add_argument("--core-only", action="store_true", help="Only install metagpt-core")

    parser.add_argument("--no-core", action="store_true", help="Do not install metagpt-core")

    parser.add_argument("--no-deps", action="store_true", help="Do not install dependencies, only the project itself")

    parser.add_argument("--sync", action="store_true", help="Synchronize all dependency versions in the lock file")

    parser.add_argument("--skip-env-check", action="store_true", help="Skip virtual environment check")

    return parser.parse_args()


def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Run command

    Args:
        cmd: Command list
        cwd: Working directory

    Returns:
        Tuple[bool, str]: (success, output)
    """
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.debug(result.stdout)
        logger.info("Command executed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command execution failed: {e.stderr}")
        return False, e.stderr


def check_virtual_env(skip_check: bool = False) -> bool:
    """Check if running in a virtual environment

    Args:
        skip_check: Whether to skip the virtual environment check

    Returns:
        bool: Whether in a virtual environment
    """
    # Simple check if in a virtual environment
    in_venv = sys.prefix != sys.base_prefix

    if in_venv:
        logger.info(f"Currently in virtual environment: {os.path.basename(sys.prefix)}")
    else:
        logger.warning(
            "Not running in a virtual environment, recommended to install and test in a virtual environment."
        )
        if not skip_check and input("Continue with installation? (y/n): ").lower() != "y":
            logger.info("Installation cancelled")
            sys.exit(0)

    return in_venv


def install_poetry():
    """Check and install poetry"""
    try:
        success, output = run_command(["poetry", "--version"])
        if success:
            logger.info(f"Poetry already installed: {output.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Poetry not installed, installing now...")
        install_cmd = [sys.executable, "-m", "pip", "install", "poetry"]

        success, _ = run_command(install_cmd)
        if not success:
            logger.error("Poetry installation failed")
            sys.exit(1)

        logger.info("Poetry installation successful")


def install_core(project_root: Path, editable: bool, no_deps: bool, sync: bool) -> bool:
    """Install metagpt-core

    Args:
        project_root: Project root directory
        editable: Whether to install in editable mode
        no_deps: Whether to skip dependencies
        sync: Whether to synchronize dependencies

    Returns:
        bool: True if installation successful, False otherwise
    """
    core_dir = project_root / "metagpt" / "core"

    if not core_dir.exists():
        logger.error(f"Core directory does not exist: {core_dir}")
        return False

    logger.info("Starting to install metagpt-core...")

    cmd = ["poetry", "install"]

    if editable:
        cmd.append("--editable")

    if no_deps:
        cmd.append("--no-deps")

    if sync:
        cmd.append("--sync")

    success, _ = run_command(cmd, str(core_dir))
    return success


def install_metagpt(
    project_root: Path, groups: List[str], editable: bool, dev: bool, no_deps: bool, sync: bool
) -> bool:
    """Install metagpt

    Args:
        project_root: Project root directory
        groups: Dependency groups to install
        editable: Whether to install in editable mode
        dev: Whether to install development dependencies
        no_deps: Whether to skip dependencies
        sync: Whether to synchronize dependencies

    Returns:
        bool: True if installation successful, False otherwise
    """
    logger.info("Starting to install metagpt...")

    cmd = ["poetry", "install"]

    if editable:
        cmd.append("--editable")

    if no_deps:
        cmd.append("--no-deps")

    if sync:
        cmd.append("--sync")

    if not dev:
        cmd.append("--without")
        cmd.append("dev")

    if groups:
        cmd.append("--with")
        cmd.append(",".join(groups))

    success, _ = run_command(cmd, str(project_root))
    return success


def check_installation() -> bool:
    """Verify installation success

    Returns:
        bool: True if verification successful, False otherwise
    """
    try:
        # Try to import metagpt.core
        check_core_cmd = [sys.executable, "-c", "import metagpt.core; print('Successfully imported MetaGPT Core')"]
        success, output = run_command(check_core_cmd)
        if success:
            logger.info(output.strip())

        else:
            return False

        # Try to import metagpt
        check_cmd = [sys.executable, "-c", "import metagpt; print('Successfully imported MetaGPT')"]
        success, output = run_command(check_cmd)
        if success:
            logger.info(output.strip())
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Import test failed: {e}")
        return False


def main():
    """Main function"""
    setup_logger()
    args = parse_args()

    # Install poetry
    install_poetry()

    # Get project root directory
    project_root = Path(__file__).parent.parent.absolute()

    # Process dependency groups
    groups = []
    if args.groups:
        groups = [g.strip() for g in args.groups.split(",") if g.strip()]

    # Install core package
    if args.core_only:
        if install_core(project_root, args.editable, args.no_deps, args.sync):
            logger.info("metagpt-core installation successful (development testing mode)")
        else:
            logger.error("metagpt-core installation failed")
        return

    # If core package and main package need to be installed together
    if not args.no_core:
        if not install_core(project_root, args.editable, args.no_deps, args.sync):
            logger.error("metagpt-core installation failed, aborting main package installation")
            return
        logger.info("metagpt-core installation successful (development testing mode)")

    # Install main package
    if install_metagpt(project_root, groups, args.editable, args.dev, args.no_deps, args.sync):
        logger.info("metagpt installation successful (development testing mode)")

        # Verify installation
        if check_installation():
            logger.info("Installation verification successful, MetaGPT is ready")
        else:
            logger.error("Installation verification failed, please check logs")
    else:
        logger.error("metagpt installation failed")


if __name__ == "__main__":
    main()

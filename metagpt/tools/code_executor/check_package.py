import importlib.util
import subprocess
import sys


def install_package(package_name):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None


def ensure_package_installed(package_name):
    if not is_package_installed(package_name):
        print(f"Package '{package_name}' is not installed. Installing...")
        install_package(package_name)
        print(f"Package '{package_name}' has been installed.")
    else:
        print(f"Package '{package_name}' is already installed.")

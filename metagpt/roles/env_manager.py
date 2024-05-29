import os
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, model_validator
from swebench import MAP_VERSION_TO_INSTALL
from swebench.harness.utils import get_environment_yml, get_requirements

from metagpt.logs import logger
from metagpt.tools.swe_agent_commands.swe_agent_utils import get_conda_base_path


class EnvManager(BaseModel):
    """
    一个环境一个manager，负责当前环境的cmd解析和处理
    env management, including env init, python executor parse and find, pip install and etc
    """

    env_name: str = ""
    repo_path: str = ""  # 需要处理的代码路径
    repo_name: str = ""
    version: str = ""
    instance: dict = {}
    conda_env_path: Path = Path(get_conda_base_path(sys.executable))
    env_python_executor: str = ""
    env_pip_executor: str = ""
    install_req: dict = {}
    python_version: str = ""
    env_req: str = ""
    reproduced_example_code: str = ""  # 用来存测试代码文件，每次git checkout 会删除写入的内容

    @model_validator(mode="after")
    def set_env(self) -> "EnvManager":
        if os.name == "nt":  # Windows
            self.env_python_executor: str = os.path.join(self.conda_env_path, self.env_name, "python")
            self.env_pip_executor: str = os.path.join(self.conda_env_path, self.env_name, "python -m pip")
        else:  # POSIX (Linux, Unix, MacOS, etc.)
            self.env_python_executor: str = os.path.join(self.conda_env_path, self.env_name, "bin/python")
            self.env_pip_executor: str = os.path.join(self.conda_env_path, self.env_name, "bin/python -m pip")
        self.parse_install_cmd(self.instance)
        self.env_req = self.get_env_info()

    @property
    def env_info(self):
        return self.env_req

    def get_env_info(self):
        command = f"{self.env_pip_executor} list"
        # 执行命令，并捕获输出
        result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding="utf-8")
        # 检查是否执行成功
        if result.returncode == 0:
            # 如果成功，返回输出结果
            return result.stdout
        else:
            # 如果失败，打印错误信息
            logger.error("Failed to get environment packages.")
            logger.error(f"Error: {result.stderr}")
        return result.stdout

    def check_conda_env_exists(self, env_name):
        # 使用 conda env list 命令列出所有环境
        result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
        logger.debug(result)
        # 检查输出中是否包含环境名
        if env_name in result.stdout:
            return True
        return False

    def delete_conda_env(self, env_name):
        try:
            # 构建删除环境的命令
            command = ["conda", "remove", "-n", env_name, "--all", "-y"]

            # 执行命令
            result = subprocess.run(command, capture_output=True, text=True)

            # 检查命令执行结果
            if result.returncode == 0:
                logger.info(f"Environment '{env_name}' successfully deleted.")
            else:
                logger.info(f"Failed to delete environment '{env_name}'.")
                logger.info(f"Error: {result.stderr}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def create_env(self):
        # 检测是否存在环境，存在即退出，直接切换
        if self.check_conda_env_exists(self.env_name):
            logger.info(self.env_python_executor)
            return
        logger.info(f"Env {self.env_name} not exists, start to create it.")

        pkgs = self.install_req["packages"]
        extra_pkgs = self.install_req["pip_packages"]

        if pkgs not in ["environment.yml", "requirements.txt"]:
            cmd = f"conda create -n {self.env_name} python={self.python_version} {pkgs} -y"
            result = subprocess.run(cmd, shell=True)

            self.env_python_executor: str = os.path.join(self.conda_env_path, self.env_name, "python")
            self.env_pip_executor: str = os.path.join(self.conda_env_path, self.env_name, "bin/python -m pip")

        if pkgs == "requirements.txt":
            cmd = f"conda create -n {self.env_name} python={self.python_version} -y"
            result = subprocess.run(cmd, shell=True)

            self.env_python_executor: str = os.path.join(self.conda_env_path, self.env_name, "python")
            self.env_pip_executor: str = os.path.join(self.conda_env_path, self.env_name, "bin/python -m pip")

            path_to_reqs = get_requirements(self.instance, self.repo_path)
            logger.info(path_to_reqs)
            install_cmd = f"{self.env_pip_executor} install -r {path_to_reqs}"
            logger.info(install_cmd)
            result = subprocess.run(install_cmd, shell=True)

        if pkgs == "environment.yml":
            path_to_reqs = get_environment_yml(
                self.instance, self.env_name, save_path=self.repo_path, python_version=self.python_version
            )
            install_cmd = f"conda env create --file {path_to_reqs}"
            result = subprocess.run(install_cmd, shell=True)

        if extra_pkgs:
            install_cmd = f"{self.env_pip_executor} {extra_pkgs}"
            result = subprocess.run(install_cmd, shell=True)
        return result.returncode

    def install_process(self, install_cmd):
        try:
            # Run installation command
            out_install = subprocess.run(install_cmd, capture_output=True, text=True, shell=True, encoding="utf-8")

            if out_install.returncode != 0:
                # Installation failed
                logger.error("Installation failed")
                return False

            # Installation successful
            logger.info("Installation successful")
            return True

        except subprocess.TimeoutExpired:
            # Installation timed out
            logger.error("Installation timed out")
            return False

        except Exception:
            # Installation failed
            logger.error("Installation failed")

            return False

    def fake_install_env(self):
        return

    def install_env(self):
        install_cmd = self.install_req["install"]
        pre_install_cmd = self.install_req["pre_install_cmd"]
        # todo: add pre_install
        logger.info(f"Running installation command: {install_cmd}")
        if install_cmd:
            self.install_process(install_cmd)
            # self.fake_install_env()
        if pre_install_cmd:
            raise NotImplementedError

    def run_in_env(self, file_path="replicate_issue.py"):
        commands = f"{self.env_python_executor} {file_path}"
        rst = subprocess.run(commands, shell=True, capture_output=True, encoding="utf-8")
        return rst

    def parse_install_cmd(self, instance: dict):
        # Get installation instructions by repo/version
        specifications = MAP_VERSION_TO_INSTALL[instance["repo"]][instance["version"]]

        install_cmd = specifications.get("install", "")
        if install_cmd:
            if "python -m pip " in install_cmd:
                install_cmd = install_cmd.replace("python -m pip", self.env_pip_executor)
            else:
                install_cmd = install_cmd.replace("pip", self.env_pip_executor)

        pre_install_cmd = specifications.get("pre_install", "")
        post_install_cmd = specifications.get("post_install", "")

        # todo: test on pre_install and post_install cases
        self.python_version = specifications["python"]
        self.install_req["packages"] = specifications.get("packages", "")
        self.install_req["pip_packages"] = specifications.get("pip_packages", "")
        self.install_req["install"] = install_cmd
        self.install_req["pre_install_cmd"] = pre_install_cmd
        self.install_req["post_install_cmd"] = post_install_cmd
        return install_cmd

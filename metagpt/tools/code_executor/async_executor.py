import asyncio
import json
import pprint
import shutil
import subprocess
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import List, Literal, Union

from loguru import logger

from metagpt.tools.code_executor.constant import SCRIPT_FILES
from metagpt.tools.code_executor.display import print_pycode_live, print_text_live

IGNORE_ERRORS = ("chose IMKClient_Modern", "chose IMKInputSession_Modern")


class AsyncCodeExecutor(object):
    def __init__(
        self,
        start_subprocess: Union[str, List[str]] = "bash",
        print_cmd: str = 'echo "{}"',
        *,
        work_dir: str = None,
        is_save_obj: bool = False,
        save_obj_cmd: str = None,
        load_obj_cmd: str = None,
        print_code_live=print_pycode_live,
    ):
        self.start_subprocess = start_subprocess
        self.print_cmd = print_cmd + "\n"
        # 双下划线的变量名不会被序列化保存到本地
        self.__process = None
        self.__cmd_stdout_event = asyncio.Event()  # 用于通知process前一个输入的command是否执行完成标准输出流
        self.__cmd_stderr_event = asyncio.Event()  # 用于通知process前一个输入的command是否执行完成标准错误流
        self._cmd_space = OrderedDict()  # cmd_id: {cmd, stddout, stderr}
        # 下面是为了磁盘保存对象而设置
        self.work_dir = work_dir
        self.__is_save_obj = is_save_obj
        self.load_obj_cmd = load_obj_cmd
        self.save_obj_cmd = save_obj_cmd
        self.__print_code_live = print_code_live
        if self.__is_save_obj:
            assert self.save_obj_cmd is not None, "save_obj_cmd should be string cmd when is_save_obj is True!"
            assert self.load_obj_cmd is not None, "load_obj_cmd should be string cmd when is_save_obj is True!"
            assert self.work_dir is not None, "work_dir should be a path when is_save_obj is True!"
            if Path(self.work_dir).exists():
                try:
                    shutil.rmtree(self.work_dir)
                    logger.info(f"已删除 {self.work_dir} 及其所有内容")
                except Exception as e:
                    logger.info(f"删除 {self.work_dir} 时发生错误: {e}")
            Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        self._executor_save_path = str(Path(self.work_dir) / "executor.json") if self.work_dir else ""

    def __str__(self) -> str:
        return self.__class__.__name__

    def manage_work_dir(self, cmd: Literal["c", "d"] = "c"):
        """管理cmd变量的共享文件目录"""
        if self.__is_save_obj:
            root = Path(self.work_dir)
            root.mkdir(parents=True, exist_ok=True)
            current_cmd_id = str(len(self._cmd_space) - 1)

            if cmd == "c":
                (root / current_cmd_id).mkdir(parents=True, exist_ok=True)

            if cmd == "d":
                shutil.rmtree(str(root))

    def obj_save_path(self, cmd_id: str) -> str:
        """每段代码内全局作用域中对象的保存路径"""
        return str(Path(self.work_dir) / cmd_id / "globals_object.pickle")

    async def load_obj(self, cmd_id: str):
        """在进程运行时载入每段代码内全局作用域的对象"""
        assert self.__process and self.__process.poll() is not None, "load_obj时进程必须处于运行状态!"
        logger.info(f"Start: load {cmd_id} objects ...")
        filepath = self.obj_save_path(cmd_id)
        load_obj_cmd = self.load_obj_cmd.format(filepath)
        await self._run(load_obj_cmd)
        logger.info(f"Done: load {cmd_id} objects!")

    def load(self, arg_names: list[str]) -> "AsyncCodeExecutor":
        """载入Executor对象和全局作用域中所有对象"""
        # 载入Executor对象
        with open(f"{self._executor_save_path}", "r") as f:
            executor_state = json.load(f)

        input_kwargs = {k: v for k, v in executor_state.items() if k in arg_names}
        self.__init__(**input_kwargs)

        # 最后一个cmd的全局作用域保存路径
        obj_path = self.obj_save_path(str(len(executor_state["_cmd_space"]) - 1))
        self.start_subprocess[-1] = self.start_subprocess[-1] + self.load_obj_cmd.format(obj_path)

        for k, v in executor_state.items():
            if k.startswith("_"):
                setattr(self, k, v)
        return self

    def save_executor(self):
        """保存Executor对象"""
        assert self.work_dir, "work_dir must be set a value, not None."
        executor_state = {k: v for k, v in self.__dict__.items() if "__" not in k}
        with open(self._executor_save_path, "w") as f:
            json.dump(executor_state, f, sort_keys=True, indent=4)

        # 添加一个.gitignore文件
        with open(str(Path(self.work_dir) / ".gitignore"), "w") as f:
            f.write("*\n")

    async def start_process(self):
        self.__process = await asyncio.create_subprocess_exec(
            *self.start_subprocess,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        asyncio.create_task(self.save_and_print_stdout(self.__process.stdout))
        asyncio.create_task(self.save_and_print_stderr(self.__process.stderr))

        self.__cmd_stdout_event.clear()
        self.__cmd_stderr_event.clear()

    async def terminate(self):
        if self.__process:
            logger.info(f"Start: Attempting to terminate the {self} process ...")
            self.__process.terminate()
            try:
                await asyncio.wait_for(self.__process.wait(), timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"{self} process did not terminate in time. Killing...")
                self.__process.kill()
        logger.info(f"Done: {self} process terminate successfully!")

        logger.debug(f"Start: Attempting to terminate the stderr and stdout tasks of {self}...")
        if self.__cmd_stderr_event:
            self.__cmd_stderr_event.set()

        if self.__cmd_stdout_event:
            self.__cmd_stdout_event.set()

        # set process is None
        self.__process = None
        logger.debug(f"Done: Stderr and stdout tasks of {self} terminate successfully!")
        if self.__is_save_obj:
            self.save_executor()

    async def reset(self):
        await self.terminate()
        await asyncio.sleep(1)
        await self.start_process()

    async def save_and_print_stdout(self, pipe: asyncio.StreamReader):
        try:
            while line := await pipe.readline():
                line = line.decode().replace(">>>", "").strip()

                if not line or line.endswith("END_OF_EXECUTION"):
                    self.__cmd_stdout_event.set()
                else:
                    cmd_id = list(self._cmd_space)[-1]
                    self._cmd_space[cmd_id]["stdout"].append("\n" + line.strip())
                    await print_text_live(line, "STDOUT")
        except Exception as e:
            print(f"系统级别错误: {e}")
        finally:
            self.__cmd_stdout_event.set()

    async def save_and_print_stderr(self, pipe: asyncio.StreamReader):
        try:
            while line := await pipe.readline():
                line = line.decode().replace(">>>", "").strip()
                if line and not line.endswith(IGNORE_ERRORS):
                    cmd_id = list(self._cmd_space)[-1]
                    self._cmd_space[cmd_id]["stderr"].append("\n" + line.strip())
                    await print_text_live(line, "STDERR")
        except Exception as e:
            print(f"系统级别错误: {e}")
        finally:
            self.__cmd_stderr_event.set()

    async def _run(self, cmds):
        if self.__process is None:
            await self.start_process()

        self.__cmd_stdout_event.clear()
        self.__cmd_stderr_event.clear()

        full_command = " ".join(cmds) + "\n\n"
        await self.__print_code_live(full_command)
        cmd_id = str(len(self._cmd_space))
        # 添加cmd到cmd_space
        self._cmd_space[cmd_id] = {}
        self._cmd_space[cmd_id]["cmd"] = full_command
        self._cmd_space[cmd_id]["stderr"] = []
        self._cmd_space[cmd_id]["stdout"] = []

        if self.__is_save_obj:
            self.manage_work_dir()
            full_command += self.save_obj_cmd.format(self.obj_save_path(cmd_id))

        full_command += self.print_cmd.format("END_OF_EXECUTION")
        logger.debug(f"Sending command: \n{full_command.strip()}")

        try:
            self.__process.stdin.write(full_command.encode())
            await self.__process.stdin.drain()  # 确保代码被发送
        except BrokenPipeError:
            logger.warning("Process has terminated. Restarting...")
            await self.start_process()
            self.__process.stdin.write(full_command.encode())
            await self.__process.stdin.drain()
        except KeyboardInterrupt:
            logger.warning("\nReceived keyboard interrupt. Terminating...")
            await self.terminate()
            raise KeyboardInterrupt()
        # Wait until execution completes
        await self.__cmd_stdout_event.wait()
        # await self.__cmd_stderr_event.wait()
        # 当处理没有stderr内容的代码时, 程序会一直卡在这里, 因此设置了2秒的超时等待, 超出2秒后就不再等待。
        # 这是一种临时的解决方案。
        await asyncio.wait([self.__cmd_stderr_event.wait()], timeout=2)

    def print_cmd_space(self):
        pprint.pprint(self._cmd_space)

    async def run(self):
        while True:
            # 从外部获取命令（通过yield）
            cmds = yield
            if cmds is None:
                continue

            if isinstance(cmds, str):
                if not cmds.endswith(SCRIPT_FILES):
                    cmds = [cmds]
                else:
                    with open(cmds, "r") as f:
                        # FIXME: python文件必须有if __name__ == "__main__":才能执行。
                        cmds = [f.read()]

            try:
                await self._run(cmds)
            except Exception as e:
                logger.error(e)
                traceback.print_exc()
                break

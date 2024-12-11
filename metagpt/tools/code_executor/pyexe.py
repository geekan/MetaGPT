from metagpt.tools.code_executor.async_executor import AsyncCodeExecutor
from metagpt.tools.code_executor.constant import PyExeConfig


class AsyncPyExecutor(AsyncCodeExecutor):
    def __init__(self, work_dir: str = None, is_save_obj: bool = False):
        super().__init__(
            PyExeConfig.start_subprocess,
            PyExeConfig.print_cmd,
            work_dir=work_dir,
            is_save_obj=is_save_obj,
            save_obj_cmd=PyExeConfig.save_obj_cmd,
            load_obj_cmd=PyExeConfig.load_obj_cmd,
        )

    def load(self):
        return super().load(["work_dir", "is_save_obj"])

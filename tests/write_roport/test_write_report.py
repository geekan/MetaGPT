import fire

from .core_report import RewriteReport


async def main(auto_run: bool = True):
    requirement = "写一份事故报告"
    di = RewriteReport(auto_run=auto_run, human_design_sop=True, use_evaluator=True)
    await di.run(f"{requirement}", upload_file="/data/wangwj-t/workspace/MetaGPT/data/data/“5.18”金达花园三期项目坍塌事故调查报告.json")


if __name__ == "__main__":
    fire.Fire(main)

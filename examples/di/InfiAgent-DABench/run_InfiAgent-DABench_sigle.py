import fire
from DABench import DABench

from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.utils.recovery_util import save_history


async def main(id=0):
    """Evaluate one task"""
    DA = DABench()
    requirement = DA.generate_formatted_prompt(id)
    di = DataInterpreter()
    result = await di.run(requirement)
    logger.info(result)
    save_history(role=di)
    _, is_correct = DA.eval(id, str(result))
    print(f"Prediction is {'correct' if is_correct else 'incorrect'}.")


if __name__ == "__main__":
    fire.Fire(main)

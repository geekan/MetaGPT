import json

import fire
from DABench import DABench

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(id=0):
    DA = DABench()
    requirement = DA.get_prompt(id)
    di = DataInterpreter()
    result = await di.run(requirement)
    prediction = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])[-1]["result"]
    is_correct = DA.eval(id, prediction)
    print(f"Prediction is {'correct' if is_correct else 'incorrect'}.")


if __name__ == "__main__":
    fire.Fire(main)

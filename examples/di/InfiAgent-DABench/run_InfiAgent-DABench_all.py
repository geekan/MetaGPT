import json

import fire
from DABench import DABench

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    """Evaluate all"""
    DA = DABench()
    id_list, predictions = [], []
    for key, value in DA.answers.items():
        requirement = DA.get_prompt(key)
        di = DataInterpreter()
        result = await di.run(requirement)
        prediction = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])[-1]["result"]
        id_list.append(key)
        predictions.append(prediction)
    print(DA.eval_all(id_list, predictions))


if __name__ == "__main__":
    fire.Fire(main)

import json

import fire
import pandas as pd
from DABench import DABench

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    """Evaluate all"""
    DA = DABench()
    id_list, predictions, labels, is_true = [], [], [], []
    for key, value in DA.answers.items():
        try:
            requirement = DA.get_prompt(key)
            di = DataInterpreter()
            result = await di.run(requirement)
            prediction = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])[-1]["result"]
            id_list.append(key)
            is_true.append(str(DA.eval(key, prediction)))
            predictions.append(str(prediction))
            labels.append(str(DA.get_answer(key)))
        except:
            id_list.append(key)
            is_true.append(str(DA.eval(key, "")))
            predictions.append(str(""))
            labels.append(str(DA.get_answer(key)))
    df = pd.DataFrame({"Label": labels, "Prediction": predictions, "T/F": is_true})

    # 将DataFrame写入Excel文件
    df.to_excel("output.xlsx", index=False)
    print(DA.eval_all(id_list, predictions))
    # 将列表转换为pandas DataFrame


if __name__ == "__main__":
    fire.Fire(main)

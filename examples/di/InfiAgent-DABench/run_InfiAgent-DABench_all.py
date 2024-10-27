import fire
import pandas as pd
from DABench import DABench

from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.utils.recovery_util import save_history


async def main():
    """Evaluate all"""
    DA = DABench()
    id_list, predictions, labels, is_true = [], [], [], []
    for key, value in DA.answers.items():
        id_list.append(key)
        labels.append(str(DA.get_answer(key)))
        try:
            requirement = DA.generate_formatted_prompt(key)
            di = DataInterpreter()
            result = await di.run(requirement)
            logger.info(result)
            save_history(role=di)
            temp_prediction, temp_istrue = DA.eval(key, str(result))
            is_true.append(str(temp_istrue))
            predictions.append(str(temp_prediction))
        except:
            is_true.append(str(DA.eval(key, "")))
            predictions.append(str(""))
    df = pd.DataFrame({"Label": labels, "Prediction": predictions, "T/F": is_true})
    df.to_excel("DABench_output.xlsx", index=False)
    print(DA.eval_all(id_list, predictions))


if __name__ == "__main__":
    fire.Fire(main)

import pandas as pd


def get_metadata(file_path):

    metadata = ""
    df = pd.read_csv(filename)
    metadata += df.describe()
    return metadata
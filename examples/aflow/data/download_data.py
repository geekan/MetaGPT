import os
import requests
import tarfile
from tqdm import tqdm

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
    
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            size = file.write(data)
            progress_bar.update(size)
    progress_bar.close()

def extract_tar_gz(filename, extract_path):
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall(path=extract_path)

url = "https://drive.google.com/uc?export=download&id=1tXp5cLw89egeKRwDuood2TPqoEWd8_C0"
filename = "aflow_data.tar.gz"
extract_path = "./"

print("Downloading data file...")
download_file(url, filename)

print("Extracting data file...")
extract_tar_gz(filename, extract_path)

print("Download and extraction completed.")

# Clean up the compressed file
os.remove(filename)
print(f"Removed {filename}")

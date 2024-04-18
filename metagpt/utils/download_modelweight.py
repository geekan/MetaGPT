import os
import requests
from pathlib import Path


def download_model(file_url: str, target_folder: str) -> str:
    file_name = file_url.split('/')[-1]  # 文件名（从URL中提取）
    file_path = os.path.join(target_folder, file_name)  # 完整的文件路径
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        # 发起GET请求下载文件
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()  # 检查请求是否成功
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                print(f'权重文件已下载并保存至 {file_path}')
        except requests.exceptions.HTTPError as err:
            print(f'权重文件下载过程中发生错误: {err}')
    return file_path

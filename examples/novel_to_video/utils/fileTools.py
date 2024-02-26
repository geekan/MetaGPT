# -*- coding: utf-8 -*-
# @Date    :
# @Author  : 宏伟（散人）
# @Desc    :
import os


# 创建小说推文用目录
def create_AINovelVideoDir(path: str):
    os.makedirs(path, exist_ok=True)
    tts_path = path + '/tts'
    os.makedirs(tts_path, exist_ok=True)
    image_path = path + '/image'
    os.makedirs(image_path, exist_ok=True)
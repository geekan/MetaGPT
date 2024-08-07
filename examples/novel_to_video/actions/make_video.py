# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :

import asyncio
import os

import cv2
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from metagpt.actions import Action

from MetaGPT.examples.novel_to_video.roles.ai_novel_video import WORKSPACE_DIR


class MakeVideo(Action):
    # 定义工作文件夹路径
    workspace: str = ""

    def __init__(self, name: str = "", workspace: str = '', *args, **kwargs):
        super().__init__(**kwargs)
        self.workspace = workspace

    async def run(self, *args, **kwargs) -> str:
        image_folder = self.workspace+'/image'
        audio_folder = self.workspace+'/tts'
        # 获取图片和音频文件的名称
        # print('image_folder:', image_folder)
        # print('audio_folder:', audio_folder)
        image_names = os.listdir(image_folder)
        audio_names = os.listdir(audio_folder)
        output_file = self.workspace + '/output_temp.mp4'
        output_file_final = self.workspace + '/output_final.mp4'
        # 初始化视频写入器
        frame_width = 768
        frame_height = 512

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video = cv2.VideoWriter(output_file, fourcc, 30, (frame_width, frame_height), True)

        for i in range(len(audio_names)):
            print(f'Processing {i}/{len(audio_names)}')
            img_path = os.path.join(image_folder, image_names[i])
            audio_path = os.path.join(audio_folder, audio_names[i])
            print('img_path:', img_path)
            print('audio_path:', audio_path)

            # 读取图片和音频
            audio = AudioFileClip(audio_path)
            audio_duration = audio.duration  # 音频的时长（秒）
            audio_fps = audio.fps  # 音频的采样率（Hz）
            # print('audio_duration:', audio_duration)
            # print('audio_fps:', audio_fps)  # 一般来说，音频的采样率是44100Hz，但可能因文件而异

            num_frames = int(audio_duration * 30)

            for _ in range(num_frames):
                img = cv2.imread(img_path)
                output_video.write(img)

        # 释放写入器
        output_video.release()

        # 写入音频
        audio_clips = []
        previous_end_time = 0
        video_clip = VideoFileClip(output_file)
        for i in range(len(audio_names)):
            # print(f'Processing {i}/{len(audio_names)}')
            audio_path = os.path.join(audio_folder, audio_names[i])
            # print('audio_path:', audio_path)

            # 读取图片和音频
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration  # 音频的时长（秒）
            audio_fps = audio_clip.fps  # 音频的采样率（Hz）
            # print('audio_duration:', audio_duration)
            # print('audio_fps:', audio_fps)  # 一般来说，音频的采样率是44100Hz，但可能因文件而异

            if i == 0:
                audio_clip = audio_clip.set_start(0)
            else:
                audio_clip = audio_clip.set_start(previous_end_time)

            previous_end_time += audio_duration

            # 将音频片段存储在列表中
            audio_clips.append(audio_clip)

        # 将音频合成到视频
        # 使用 concatenate_audio clips 方法连接音频片段
        final_audio = concatenate_audioclips(audio_clips)

        # 将最终音频附加到视频
        video_clip = video_clip.set_audio(final_audio)

        # 保存输出视频
        video_clip.write_videofile(output_file_final, codec='libx264', audio_codec='aac')

        # 删除临时文件
        if os.path.exists(output_file):
            os.remove(output_file)

        return output_file_final


async def main():
    action = MakeVideo(workspace=WORKSPACE_DIR)
    res = await action.run()
    print(res)


if __name__ == '__main__':
    asyncio.run(main())
